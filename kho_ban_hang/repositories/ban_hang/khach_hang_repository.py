from datetime import date
from ..phan_trang import lay_trang
from ..tim_kiem import chuan_hoa

from kho_ban_hang.domain.khach_hang import KhachHang, KhachThuong, KhachVIP


class KhachHangRepository:
    def __init__(self, ket_noi_db):
        self.db = ket_noi_db

    def tim_theo_ma(self, ma_kh) -> KhachHang | None:
        r = self.db.execute("SELECT * FROM khach_hang WHERE ma_kh=?", (ma_kh,)).fetchone()
        if r is None:
            return None
        args = (r["ma_kh"], r["ho_ten"], r["so_dien_thoai"], r["dia_chi"], r["diem_tich_luy"])
        if r["hang"] == "VIP":
            return KhachVIP(*args, ngay_len_hang=date.fromisoformat(r["ngay_len_hang"])
                            if r["ngay_len_hang"] else None)
        return KhachThuong(*args)

    def luu(self, kh: KhachHang) -> None:
        vip = kh.la_vip
        self.db.execute(
            """INSERT INTO khach_hang(ma_kh,ho_ten,so_dien_thoai,dia_chi,diem_tich_luy,hang,ngay_len_hang)
               VALUES (?,?,?,?,?,?,?)
               ON CONFLICT(ma_kh) DO UPDATE SET ho_ten=excluded.ho_ten,
                 so_dien_thoai=excluded.so_dien_thoai, dia_chi=excluded.dia_chi,
                 diem_tich_luy=excluded.diem_tich_luy""",   # hạng chỉ đổi qua nang_hang_vip
            (kh.ma_kh, kh.ho_ten, kh.so_dien_thoai, kh.dia_chi, kh.diem_tich_luy,
             "VIP" if vip else "THUONG",
             kh.ngay_len_hang.isoformat() if vip and kh.ngay_len_hang else None))

    def nang_hang_vip(self, ma_kh: str, ngay: date) -> None:
        self.db.execute("UPDATE khach_hang SET hang='VIP', ngay_len_hang=? WHERE ma_kh=?",
                        (ngay.isoformat(), ma_kh))

    def cap_ma_moi(self) -> str:
        self.db.execute("INSERT OR IGNORE INTO bo_dem_ma VALUES ('khach_hang', 0)")
        row = self.db.execute(
            "SELECT MAX(CAST(SUBSTR(ma_kh, 3) AS INTEGER)) FROM khach_hang WHERE ma_kh LIKE 'KH%'"
        ).fetchone()
        max_hien_tai = row[0] if (row and row[0] is not None) else 0
        dem_hien_tai = self.db.execute(
            "SELECT gia_tri FROM bo_dem_ma WHERE ten='khach_hang'"
        ).fetchone()[0]
        if max_hien_tai > dem_hien_tai:
            self.db.execute("UPDATE bo_dem_ma SET gia_tri = ? WHERE ten='khach_hang'", (max_hien_tai,))
        self.db.execute("UPDATE bo_dem_ma SET gia_tri = gia_tri + 1 WHERE ten='khach_hang'")
        n = self.db.execute("SELECT gia_tri FROM bo_dem_ma WHERE ten='khach_hang'").fetchone()[0]
        return f"KH{n:03d}"

    def tim_tat_ca(self, page=None, page_size=20) -> list[dict]:
        sql = """
            SELECT kh.ma_kh, kh.ho_ten, kh.so_dien_thoai, kh.dia_chi,
                   kh.diem_tich_luy, kh.hang, kh.ngay_len_hang,
                   COALESCE(SUM(CASE WHEN dh.trang_thai = 'DA_THANH_TOAN' THEN hd.tong_thanh_toan ELSE 0 END), 0) AS tong_chi_tieu,
                   COUNT(CASE WHEN dh.trang_thai = 'DA_THANH_TOAN' THEN 1 END) AS so_don_thanh_cong
            FROM khach_hang kh
            LEFT JOIN don_hang dh ON kh.ma_kh = dh.ma_kh
            LEFT JOIN hoa_don hd ON dh.ma_don = hd.ma_don
            GROUP BY kh.ma_kh
            ORDER BY kh.ma_kh
        """
        if page is not None:
            return lay_trang(self.db, sql, (), page, page_size)
        rows = self.db.execute(sql).fetchall()
        return [dict(r) for r in rows]

    def tra_cuu(self, tu_khoa: str, page=None, page_size=20) -> list[dict]:
        tu_khoa = (tu_khoa or "").strip()
        if not tu_khoa:
            return self.tim_tat_ca(page, page_size)
        like = chuan_hoa(tu_khoa)
        sql = """
            SELECT DISTINCT kh.ma_kh, kh.ho_ten, kh.so_dien_thoai, kh.dia_chi,
                   kh.diem_tich_luy, kh.hang, kh.ngay_len_hang,
                   COALESCE(sub.tong_chi_tieu, 0) AS tong_chi_tieu,
                   COALESCE(sub.so_don_thanh_cong, 0) AS so_don_thanh_cong
            FROM khach_hang kh
            LEFT JOIN (
                SELECT dh2.ma_kh,
                       SUM(CASE WHEN dh2.trang_thai = 'DA_THANH_TOAN' THEN hd2.tong_thanh_toan ELSE 0 END) AS tong_chi_tieu,
                       COUNT(CASE WHEN dh2.trang_thai = 'DA_THANH_TOAN' THEN 1 END) AS so_don_thanh_cong
                FROM don_hang dh2
                LEFT JOIN hoa_don hd2 ON dh2.ma_don = hd2.ma_don
                GROUP BY dh2.ma_kh
            ) sub ON kh.ma_kh = sub.ma_kh
            LEFT JOIN don_hang dh ON kh.ma_kh = dh.ma_kh
            WHERE instr(chuan_hoa(kh.ma_kh || ' ' || kh.ho_ten || ' ' || kh.so_dien_thoai || ' ' || COALESCE(dh.ma_don,'')),?)>0
            ORDER BY kh.ma_kh
        """
        if page is not None:
            return lay_trang(self.db, sql, (like,), page, page_size)
        rows = self.db.execute(sql, (like,)).fetchall()
        return [dict(r) for r in rows]

    def lay_lich_su_don_hang(self, ma_kh: str) -> list[dict]:
        sql = """
            SELECT dh.ma_don, dh.ma_nv, dh.ngay_lap, dh.trang_thai, dh.giam_hang_khach, dh.giam_khuyen_mai,
                   COALESCE(hd.tong_thanh_toan, MAX(0, COALESCE(ct.tam_tinh,0)-dh.giam_hang_khach-dh.giam_khuyen_mai)) AS tong_thanh_toan,
                   nv.ho_ten AS ten_nv
            FROM don_hang dh
            LEFT JOIN hoa_don hd ON dh.ma_don = hd.ma_don
            LEFT JOIN nhan_vien nv ON dh.ma_nv = nv.ma_nv
            LEFT JOIN (
                SELECT ma_don,SUM(so_luong*don_gia) AS tam_tinh
                FROM chi_tiet_don_hang GROUP BY ma_don
            ) ct ON ct.ma_don=dh.ma_don
            WHERE dh.ma_kh = ?
            ORDER BY dh.ngay_lap DESC, dh.ma_don DESC
        """
        rows = self.db.execute(sql, (ma_kh,)).fetchall()
        return [dict(r) for r in rows]
