from ...domain.danh_muc import DanhMuc
from ...domain.enums_kho import TrangThaiDanhMuc
from ...domain.errors import KhongTimThayError


class DanhMucRepository:
    def __init__(self, ket_noi_db):
        self.ket_noi_db = ket_noi_db

    def tim_theo_ma(self, ma_dm: str) -> DanhMuc:
        row = self.ket_noi_db.execute("SELECT * FROM danh_muc WHERE ma_dm = ?", (ma_dm,)).fetchone()
        if row is None:
            raise KhongTimThayError(f"Không tìm thấy danh mục {ma_dm}.")
        return DanhMuc(row["ma_dm"], row["ten_dm"], row["mo_ta"], TrangThaiDanhMuc(row["trang_thai"]))

    def luu(self, danh_muc: DanhMuc) -> None:
        self.ket_noi_db.execute(
            """INSERT INTO danh_muc VALUES (?, ?, ?, ?)
               ON CONFLICT (ma_dm) DO UPDATE SET ten_dm=excluded.ten_dm,
               mo_ta=excluded.mo_ta, trang_thai=excluded.trang_thai""",
            (danh_muc.ma_dm, danh_muc.ten_dm, danh_muc.mo_ta, danh_muc.trang_thai),
        )
