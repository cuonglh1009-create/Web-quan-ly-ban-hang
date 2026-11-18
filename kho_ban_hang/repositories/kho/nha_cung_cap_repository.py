from ...domain.enums_kho import TrangThaiNhaCungCap
from ...domain.errors import KhongTimThayError
from ...domain.nha_cung_cap import NhaCungCap


class NhaCungCapRepository:
    def __init__(self, ket_noi_db):
        self.ket_noi_db = ket_noi_db

    def tim_theo_ma(self, ma_ncc: str) -> NhaCungCap:
        row = self.ket_noi_db.execute("SELECT * FROM nha_cung_cap WHERE ma_ncc = ?", (ma_ncc,)).fetchone()
        if row is None:
            raise KhongTimThayError(f"Không tìm thấy nhà cung cấp {ma_ncc}.", "ma_ncc")
        return self._tao(row)

    def tim_tat_ca(self) -> list[NhaCungCap]:
        return [self._tao(row) for row in self.ket_noi_db.execute("SELECT * FROM nha_cung_cap ORDER BY ma_ncc")]

    def luu(self, ncc: NhaCungCap) -> None:
        self.ket_noi_db.execute(
            """INSERT INTO nha_cung_cap VALUES (?, ?, ?, ?, ?)
               ON CONFLICT (ma_ncc) DO UPDATE SET ten_ncc=excluded.ten_ncc,
               so_dien_thoai=excluded.so_dien_thoai, dia_chi=excluded.dia_chi, trang_thai=excluded.trang_thai""",
            (ncc.ma_ncc, ncc.ten_ncc, ncc.so_dien_thoai, ncc.dia_chi, ncc.trang_thai),
        )

    @staticmethod
    def _tao(row):
        return NhaCungCap(
            row["ma_ncc"], row["ten_ncc"], row["so_dien_thoai"],
            row["dia_chi"], TrangThaiNhaCungCap(row["trang_thai"]),
        )
