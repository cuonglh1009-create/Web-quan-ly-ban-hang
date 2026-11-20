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

    @staticmethod
    def _bo_loc(ma_lo, ma_sp):
        # Chỉ ghép tên cột cố định; mọi giá trị đầu vào đều truyền bằng tham số.
        dieu_kien, tham_so = [], []
        for cot, gia_tri in (("ma_lo", ma_lo), ("ma_sp", ma_sp)):
            if gia_tri is not None:
                dieu_kien.append(f"lo.{cot} = ?")
                tham_so.append(gia_tri)
        return (" AND ".join(dieu_kien) or "1=1"), tham_so

    def tim(self, ma_lo: str | None = None, ma_sp: str | None = None) -> list[LoHang]:
        dieu_kien, tham_so = self._bo_loc(ma_lo, ma_sp)
        ds = self.ket_noi_db.execute(
            "SELECT lo.* FROM lo_hang lo WHERE " + dieu_kien + " ORDER BY lo.ma_lo", tham_so,
        )
        return self._tao_nhieu(ds.fetchall())

    def tim_con_ton(self) -> list[LoHang]:
        return self._tao_nhieu(self.ket_noi_db.execute(
            "SELECT * FROM lo_hang WHERE so_luong_con_lai > 0 ORDER BY han_su_dung, ma_lo"
        ).fetchall())

    def tim_voi_so_dang_giu(self, ma_lo: str | None, ma_sp: str | None, uu_tien_xuat: bool = False) -> list[tuple[LoHang, int]]:
        dieu_kien, tham_so = self._bo_loc(ma_lo, ma_sp)
        rows = self.ket_noi_db.execute(
            """SELECT lo.*, COALESCE((
                   SELECT SUM(giu.so_luong) FROM giu_hang AS giu WHERE giu.ma_lo = lo.ma_lo
               ), 0) AS dang_giu
               FROM lo_hang AS lo
               WHERE """ + dieu_kien + " ORDER BY " + ("lo.han_su_dung IS NULL, lo.han_su_dung, lo.ngay_nhap, lo.ma_lo" if uu_tien_xuat else "lo.ma_lo"),
            tham_so,
        ).fetchall()
        return list(zip(self._tao_nhieu(rows), (row["dang_giu"] for row in rows)))

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

    def tim_dang_giu(self, ma_don: str):
        rows = self.ket_noi_db.execute(
            """SELECT lo.*, giu.so_luong AS so_giu FROM giu_hang giu
               JOIN lo_hang lo ON lo.ma_lo = giu.ma_lo
               WHERE giu.ma_don = ? ORDER BY lo.ma_lo""", (ma_don,)
        ).fetchall()
        return list(zip(self._tao_nhieu(rows), (row["so_giu"] for row in rows)))

    def _tao_nhieu(self, rows):
        san_pham = self.san_pham_repo.tim_nhieu(row["ma_sp"] for row in rows)
        return [self._tao(row, san_pham[row["ma_sp"]]) for row in rows]

    def _tao(self, row, san_pham):
        return LoHang(
            row["ma_lo"], san_pham, date.fromisoformat(row["ngay_nhap"]),
            date.fromisoformat(row["ngay_san_xuat"]) if row["ngay_san_xuat"] else None,
            date.fromisoformat(row["han_su_dung"]) if row["han_su_dung"] else None,
            row["so_luong_con_lai"], row["gia_nhap"],
        )
