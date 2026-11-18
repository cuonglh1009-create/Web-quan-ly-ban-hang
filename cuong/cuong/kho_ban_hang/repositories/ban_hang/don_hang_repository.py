from datetime import date

from kho_ban_hang.domain.don_hang import ChiTietDonHang, DonHang
from kho_ban_hang.domain.enums_chung import TrangThaiDonHang


class DonHangRepository:
    def __init__(self, ket_noi_db, nhan_vien_repo, khach_repo, km_repo, tra_cuu_san_pham):
        self.db, self.nv, self.kh, self.km, self.sp = (
            ket_noi_db, nhan_vien_repo, khach_repo, km_repo, tra_cuu_san_pham)

    def cap_ma_moi(self) -> str:
        """Gọi trong GiaoDich (đang giữ khóa ghi) nên không cấp trùng."""
        self.db.execute("INSERT OR IGNORE INTO bo_dem_ma VALUES ('don_hang', 0)")
        self.db.execute("UPDATE bo_dem_ma SET gia_tri = gia_tri + 1 WHERE ten='don_hang'")
        n = self.db.execute("SELECT gia_tri FROM bo_dem_ma WHERE ten='don_hang'").fetchone()[0]
        return f"DH{n:06d}"

    def tim_theo_ma(self, ma_don) -> DonHang | None:
        r = self.db.execute("SELECT * FROM don_hang WHERE ma_don=?", (ma_don,)).fetchone()
        if r is None:
            return None
        chi_tiet = []
        for c in self.db.execute("SELECT * FROM chi_tiet_don_hang WHERE ma_don=? ORDER BY rowid",
                                 (ma_don,)):
            sp = self.sp.tim_theo_ma(c["ma_sp"])
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
