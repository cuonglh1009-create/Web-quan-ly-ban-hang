from datetime import date
from decimal import Decimal

from kho_ban_hang.domain.enums_chung import TrangThaiKhuyenMai
from kho_ban_hang.domain.khuyen_mai import KhuyenMai, KhuyenMaiPhanTram, KhuyenMaiTienMat


class KhuyenMaiRepository:
    def __init__(self, ket_noi_db):
        self.db = ket_noi_db

    def tim_theo_ma(self, ma_km) -> KhuyenMai | None:
        r = self.db.execute("SELECT * FROM khuyen_mai WHERE ma_km=?", (ma_km,)).fetchone()
        if r is None:
            return None
        chung = (r["ma_km"], r["ten_km"], date.fromisoformat(r["ngay_bat_dau"]),
                 date.fromisoformat(r["ngay_ket_thuc"]), r["gia_tri_don_toi_thieu"],
                 TrangThaiKhuyenMai(r["trang_thai"]))
        if r["loai"] == "PHAN_TRAM":
            return KhuyenMaiPhanTram(*chung, phan_tram_giam=Decimal(r["phan_tram_giam"]),
                                     giam_toi_da=r["giam_toi_da"])
        return KhuyenMaiTienMat(*chung, so_tien_giam=r["so_tien_giam"])

    def luu(self, km: KhuyenMai) -> None:
        phan_tram = isinstance(km, KhuyenMaiPhanTram)
        self.db.execute(
            """INSERT OR REPLACE INTO khuyen_mai VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (km.ma_km, km.ten_km, "PHAN_TRAM" if phan_tram else "TIEN_MAT",
             km.ngay_bat_dau.isoformat(), km.ngay_ket_thuc.isoformat(),
             km.gia_tri_don_toi_thieu, km.trang_thai.value,
             str(km.phan_tram_giam) if phan_tram else None,
             km.giam_toi_da if phan_tram else None,
             None if phan_tram else km.so_tien_giam))
