from kho_ban_hang.domain.enums_chung import TrangThaiNhanVien, VaiTro
from kho_ban_hang.domain.nhan_vien import NhanVien


class NhanVienRepository:
    def __init__(self, ket_noi_db):
        self.db = ket_noi_db

    @staticmethod
    def _tu_dong(r) -> NhanVien | None:
        if r is None:
            return None
        return NhanVien(r["ma_nv"], r["ho_ten"], VaiTro(r["vai_tro"]), r["ten_dang_nhap"],
                        r["mat_khau_hash"], TrangThaiNhanVien(r["trang_thai"]))

    def tim_theo_ma(self, ma_nv):
        return self._tu_dong(self.db.execute("SELECT * FROM nhan_vien WHERE ma_nv=?", (ma_nv,)).fetchone())

    def tim_theo_ten_dang_nhap(self, ten_dang_nhap):
        return self._tu_dong(self.db.execute(
            "SELECT * FROM nhan_vien WHERE ten_dang_nhap=?", (ten_dang_nhap,)).fetchone())

    def luu(self, nv: NhanVien) -> None:   # dùng cho seed
        self.db.execute(
            """INSERT INTO nhan_vien VALUES (?,?,?,?,?,?)
               ON CONFLICT(ma_nv) DO UPDATE SET ho_ten=excluded.ho_ten,
                 ten_dang_nhap=excluded.ten_dang_nhap, mat_khau_hash=excluded.mat_khau_hash,
                 vai_tro=excluded.vai_tro, trang_thai=excluded.trang_thai""",
            (nv.ma_nv, nv.ho_ten, nv.ten_dang_nhap, nv.mat_khau_hash,
             nv.vai_tro.value, nv.trang_thai.value))
