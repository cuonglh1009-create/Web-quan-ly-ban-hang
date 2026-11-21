from datetime import date
from ..phan_trang import lay_trang
from ..tim_kiem import chuan_hoa

from kho_ban_hang.domain.don_hang import ChiTietDonHang, DonHang
from kho_ban_hang.domain.enums_chung import TrangThaiDonHang


class DonHangRepository:
    def __init__(self, ket_noi_db, nhan_vien_repo, khach_repo, km_repo, tra_cuu_san_pham):
        self.db, self.nv, self.kh, self.km, self.sp = (
            ket_noi_db, nhan_vien_repo, khach_repo, km_repo, tra_cuu_san_pham)

    def cap_ma_moi(self) -> str:
        """Gọi trong GiaoDich (đang giữ khóa ghi) nên không cấp trùng."""
        self.db.execute("INSERT OR IGNORE INTO bo_dem_ma VALUES ('don_hang', 0)")
        row = self.db.execute(
            "SELECT MAX(CAST(SUBSTR(ma_don, 3) AS INTEGER)) FROM don_hang WHERE ma_don LIKE 'DH%'"
        ).fetchone()
        max_hien_tai = row[0] if (row and row[0] is not None) else 0
        dem_hien_tai = self.db.execute(
            "SELECT gia_tri FROM bo_dem_ma WHERE ten='don_hang'"
        ).fetchone()[0]
        if max_hien_tai > dem_hien_tai:
            self.db.execute("UPDATE bo_dem_ma SET gia_tri = ? WHERE ten='don_hang'", (max_hien_tai,))
        self.db.execute("UPDATE bo_dem_ma SET gia_tri = gia_tri + 1 WHERE ten='don_hang'")
        n = self.db.execute("SELECT gia_tri FROM bo_dem_ma WHERE ten='don_hang'").fetchone()[0]
        return f"DH{n:06d}"

    def lay_ma_du_kien(self) -> str:
        self.db.execute("INSERT OR IGNORE INTO bo_dem_ma VALUES ('don_hang', 0)")
        row = self.db.execute(
            "SELECT MAX(CAST(SUBSTR(ma_don, 3) AS INTEGER)) FROM don_hang WHERE ma_don LIKE 'DH%'"
        ).fetchone()
        max_hien_tai = row[0] if (row and row[0] is not None) else 0
        dem_hien_tai = self.db.execute(
            "SELECT gia_tri FROM bo_dem_ma WHERE ten='don_hang'"
        ).fetchone()[0]
        n = max(max_hien_tai, dem_hien_tai) + 1
        return f"DH{n:06d}"

    def lay_danh_sach(self, trang_thai: str | None = None, tu_khoa: str | None = None, page=None, page_size=20, ma_nv=None) -> list[dict]:
        params = []
        where_clauses = []
        if trang_thai:
            where_clauses.append("dh.trang_thai = ?")
            params.append(trang_thai)
        if tu_khoa:
            where_clauses.append("instr(chuan_hoa(dh.ma_don || ' ' || COALESCE(kh.ho_ten,'') || ' ' || COALESCE(kh.so_dien_thoai,'')),?)>0")
            params.append(chuan_hoa(tu_khoa))
        if ma_nv:
            where_clauses.append("dh.ma_nv = ?");params.append(ma_nv)
        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        sql = f"""
            SELECT dh.ma_don, dh.ngay_lap, dh.trang_thai, dh.giam_hang_khach, dh.giam_khuyen_mai,
                   dh.ma_nv, nv.ho_ten AS ten_nv,
                   dh.ma_kh, kh.ho_ten AS ten_kh, kh.so_dien_thoai AS sdt_kh, kh.hang AS hang_kh,
                   COALESCE(ct.tong_tien_hang, 0) AS tong_tien_hang,
                   COALESCE(hd.tong_thanh_toan, MAX(0, COALESCE(ct.tong_tien_hang, 0) - dh.giam_hang_khach - dh.giam_khuyen_mai)) AS tong_thanh_toan,
                   hd.ma_hd
            FROM don_hang dh
            LEFT JOIN nhan_vien nv ON dh.ma_nv = nv.ma_nv
            LEFT JOIN khach_hang kh ON dh.ma_kh = kh.ma_kh
            LEFT JOIN hoa_don hd ON dh.ma_don = hd.ma_don
            LEFT JOIN (
                SELECT ma_don, SUM(so_luong * don_gia) AS tong_tien_hang
                FROM chi_tiet_don_hang
                GROUP BY ma_don
            ) ct ON dh.ma_don = ct.ma_don
            {where_sql}
            ORDER BY dh.ngay_lap DESC, dh.ma_don DESC
        """
        if page is not None:
            return lay_trang(self.db, sql, params, page, page_size)
        rows = self.db.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def thong_ke_doanh_thu(self, kieu: str = "ngay") -> list[dict]:
        kieu = (kieu or "ngay").lower()
        if kieu == "nam":
            dinh_dang = "SUBSTR(dh.ngay_lap, 1, 4)"
        elif kieu == "thang":
            dinh_dang = "SUBSTR(dh.ngay_lap, 1, 7)"
        else:
            dinh_dang = "dh.ngay_lap"
        sql = f"""
            SELECT {dinh_dang} AS thoi_gian,
                   COUNT(DISTINCT dh.ma_don) AS so_don,
                   COALESCE(SUM(hd.tong_tien_truoc_giam), 0) AS tong_tien_hang,
                   COALESCE(SUM(hd.tong_giam), 0) AS tong_giam,
                   COALESCE(SUM(hd.tong_thanh_toan), 0) AS doanh_thu
            FROM don_hang dh
            JOIN hoa_don hd ON dh.ma_don = hd.ma_don
            WHERE dh.trang_thai = 'DA_THANH_TOAN'
            GROUP BY {dinh_dang}
            ORDER BY thoi_gian DESC
        """
        rows = self.db.execute(sql).fetchall()
        return [dict(r) for r in rows]

    def thong_ke_san_pham_ban_chay(self) -> list[dict]:
        sql = """
            SELECT ct.ma_sp,
                   COALESCE(sp.ten_sp, ct.ma_sp) AS ten_sp,
                   COALESCE(sp.don_vi_tinh, '') AS don_vi_tinh,
                   SUM(ct.so_luong) AS tong_so_luong,
                   SUM(ct.so_luong * ct.don_gia) AS tong_doanh_thu
            FROM chi_tiet_don_hang ct
            JOIN don_hang dh ON ct.ma_don = dh.ma_don
            LEFT JOIN san_pham sp ON ct.ma_sp = sp.ma_sp
            WHERE dh.trang_thai = 'DA_THANH_TOAN'
            GROUP BY ct.ma_sp
            ORDER BY tong_so_luong DESC, tong_doanh_thu DESC
        """
        rows = self.db.execute(sql).fetchall()
        return [dict(r) for r in rows]

    def tim_theo_ma(self, ma_don) -> DonHang | None:
        r = self.db.execute("SELECT * FROM don_hang WHERE ma_don=?", (ma_don,)).fetchone()
        if r is None:
            return None
        chi_tiet = []
        rows = self.db.execute("SELECT * FROM chi_tiet_don_hang WHERE ma_don=? ORDER BY rowid", (ma_don,)).fetchall()
        products = self.sp.tim_nhieu(row["ma_sp"] for row in rows)
        for c in rows:
            sp = products[c["ma_sp"]]
            chi_tiet.append(ChiTietDonHang(sp, c["so_luong"], c["don_gia"]))  # giá đã chốt
        return DonHang(
            r["ma_don"], date.fromisoformat(r["ngay_lap"]), TrangThaiDonHang(r["trang_thai"]),
            self.nv.tim_theo_ma(r["ma_nv"]),
            self.kh.tim_theo_ma(r["ma_kh"]) if r["ma_kh"] else None,
            chi_tiet, self.km.tim_theo_ma(r["ma_km"]) if r["ma_km"] else None,
            r["giam_hang_khach"], r["giam_khuyen_mai"])

    def luu(self, don: DonHang) -> None:
        da_co = self.db.execute("SELECT 1 FROM don_hang WHERE ma_don=?", (don.ma_don,)).fetchone()
        ma_kh = don.khach_hang.ma_kh if don.khach_hang else None
        ma_km = don.khuyen_mai.ma_km if don.khuyen_mai else None
        if da_co:   # dòng hàng bất biến sau khi lập; chỉ cập nhật phần đầu đơn
            self.db.execute(
                "UPDATE don_hang SET trang_thai=?, ma_km=?, giam_hang_khach=?, giam_khuyen_mai=? "
                "WHERE ma_don=?",
                (don.trang_thai.value, ma_km, don.giam_hang_khach, don.giam_khuyen_mai, don.ma_don))
            return
        self.db.execute(
            "INSERT INTO don_hang VALUES (?,?,?,?,?,?,?,?)",
            (don.ma_don, don.ngay_lap.isoformat(), don.trang_thai.value, don.nhan_vien.ma_nv,
             ma_kh, ma_km, don.giam_hang_khach, don.giam_khuyen_mai))
        self.db.executemany(
            "INSERT INTO chi_tiet_don_hang VALUES (?,?,?,?)",
            [(don.ma_don, c.san_pham.ma_sp, c.so_luong, c.don_gia) for c in don.chi_tiet])
