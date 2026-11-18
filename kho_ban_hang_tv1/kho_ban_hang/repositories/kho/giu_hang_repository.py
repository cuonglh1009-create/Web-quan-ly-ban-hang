from ...domain.lo_hang import GiuHang


class GiuHangRepository:
    def __init__(self, ket_noi_db, lo_hang_repo):
        self.ket_noi_db = ket_noi_db
        self.lo_hang_repo = lo_hang_repo

    def tim_theo_don(self, ma_don: str) -> list[GiuHang]:
        rows = self.ket_noi_db.execute(
            "SELECT ma_lo, so_luong FROM giu_hang WHERE ma_don = ? ORDER BY ma_lo", (ma_don,)
        )
        return [GiuHang(ma_don, self.lo_hang_repo.tim_theo_ma(row["ma_lo"]), row["so_luong"]) for row in rows]

    def tong_dang_giu(self, ma_lo: str) -> int:
        return self.ket_noi_db.execute(
            "SELECT COALESCE(SUM(so_luong), 0) FROM giu_hang WHERE ma_lo = ?", (ma_lo,)
        ).fetchone()[0]

    def luu_nhieu(self, ds: list[GiuHang]) -> None:
        self.ket_noi_db.executemany(
            "INSERT INTO giu_hang (ma_don, ma_lo, so_luong) VALUES (?, ?, ?)",
            [(giu.ma_don, giu.lo_hang.ma_lo, giu.so_luong) for giu in ds],
        )

    def xoa_theo_don(self, ma_don: str) -> None:
        self.ket_noi_db.execute("DELETE FROM giu_hang WHERE ma_don = ?", (ma_don,))
