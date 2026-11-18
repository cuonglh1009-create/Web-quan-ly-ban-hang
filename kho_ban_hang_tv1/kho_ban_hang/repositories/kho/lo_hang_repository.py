from datetime import date

from ...domain.errors import KhongTimThayError
from ...domain.lo_hang import LoHang


class LoHangRepository:
    def __init__(self, ket_noi_db, san_pham_repo):
        self.ket_noi_db = ket_noi_db
        self.san_pham_repo = san_pham_repo

    def tim_theo_ma(self, ma_lo: str) -> LoHang:
        ds = self.tim(ma_lo=ma_lo)
        if not ds:
            raise KhongTimThayError(f"Không tìm thấy lô {ma_lo}.", "ma_lo")
        return ds[0]

    def tim_theo_san_pham(self, ma_sp: str) -> list[LoHang]:
        return self.tim(ma_sp=ma_sp)

    def tim(self, ma_lo: str | None = None, ma_sp: str | None = None) -> list[LoHang]:
        ds = self.ket_noi_db.execute(
            """SELECT * FROM lo_hang WHERE (? IS NULL OR ma_lo = ?) AND (? IS NULL OR ma_sp = ?)
               ORDER BY ma_lo""",
            (ma_lo, ma_lo, ma_sp, ma_sp),
        )
        return [self._tao(row) for row in ds]

    def tim_con_ton(self) -> list[LoHang]:
        return [self._tao(row) for row in self.ket_noi_db.execute(
            "SELECT * FROM lo_hang WHERE so_luong_con_lai > 0 ORDER BY han_su_dung, ma_lo"
        )]

    def tim_voi_so_dang_giu(self, ma_lo: str | None, ma_sp: str | None) -> list[tuple[LoHang, int]]:
        rows = self.ket_noi_db.execute(
            """SELECT lo.*, COALESCE((
                   SELECT SUM(giu.so_luong) FROM giu_hang AS giu WHERE giu.ma_lo = lo.ma_lo
               ), 0) AS dang_giu
               FROM lo_hang AS lo
               WHERE (? IS NULL OR lo.ma_lo = ?) AND (? IS NULL OR lo.ma_sp = ?)
               ORDER BY lo.ma_lo""",
            (ma_lo, ma_lo, ma_sp, ma_sp),
        ).fetchall()
        return [(self._tao(row), row["dang_giu"]) for row in rows]

    def ton_tai_ma_lo(self, ma_lo: str) -> bool:
        return self.ket_noi_db.execute("SELECT 1 FROM lo_hang WHERE ma_lo=?", (ma_lo,)).fetchone() is not None

    def them(self, lo: LoHang) -> None:
        self.ket_noi_db.execute(
            "INSERT INTO lo_hang VALUES (?, ?, ?, ?, ?, ?, ?)",
            (lo.ma_lo, lo.san_pham.ma_sp, lo.ngay_nhap.isoformat(),
             lo.ngay_san_xuat.isoformat() if lo.ngay_san_xuat else None,
             lo.han_su_dung.isoformat() if lo.han_su_dung else None, lo.so_luong_con_lai, lo.gia_nhap),
        )

    def luu(self, lo: LoHang) -> None:
        self.ket_noi_db.execute(
            "UPDATE lo_hang SET so_luong_con_lai = ? WHERE ma_lo = ?",
            (lo.so_luong_con_lai, lo.ma_lo),
        )

    def _tao(self, row):
        return LoHang(
            row["ma_lo"], self.san_pham_repo.tim_theo_ma(row["ma_sp"]), date.fromisoformat(row["ngay_nhap"]),
            date.fromisoformat(row["ngay_san_xuat"]) if row["ngay_san_xuat"] else None,
            date.fromisoformat(row["han_su_dung"]) if row["han_su_dung"] else None,
            row["so_luong_con_lai"], row["gia_nhap"],
        )
