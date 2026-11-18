from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal, ROUND_FLOOR

from kho_ban_hang.domain.enums_chung import TrangThaiKhuyenMai


class KhuyenMai(ABC):
    def __init__(self, ma_km: str, ten_km: str, ngay_bat_dau: date, ngay_ket_thuc: date,
                 gia_tri_don_toi_thieu: int = 0,
                 trang_thai: TrangThaiKhuyenMai = TrangThaiKhuyenMai.HOAT_DONG):
        self.ma_km, self.ten_km = ma_km, ten_km
        self.ngay_bat_dau, self.ngay_ket_thuc = ngay_bat_dau, ngay_ket_thuc
        self.gia_tri_don_toi_thieu, self.trang_thai = gia_tri_don_toi_thieu, trang_thai

    def ap_dung_duoc(self, tam_tinh: int, ngay: date) -> bool:  # QT07
        return (self.trang_thai == TrangThaiKhuyenMai.HOAT_DONG
                and self.ngay_bat_dau <= ngay <= self.ngay_ket_thuc   # gồm hai đầu mút
                and tam_tinh >= self.gia_tri_don_toi_thieu)

    @abstractmethod
    def tinh_giam(self, so_tien_sau_ck: int) -> int: ...


class KhuyenMaiPhanTram(KhuyenMai):
    """phan_tram_giam theo đơn vị phần trăm: 10 nghĩa là 10%."""

    def __init__(self, *args, phan_tram_giam: Decimal, giam_toi_da: int | None = None, **kw):
        super().__init__(*args, **kw)
        if not (Decimal(0) < phan_tram_giam <= Decimal(100)):
            raise ValueError("phan_tram_giam phải trong (0, 100]")
        self.phan_tram_giam, self.giam_toi_da = phan_tram_giam, giam_toi_da

    def tinh_giam(self, so_tien_sau_ck: int) -> int:
        giam = int((Decimal(so_tien_sau_ck) * self.phan_tram_giam / 100)
                   .to_integral_value(ROUND_FLOOR))
        if self.giam_toi_da is not None:
            giam = min(giam, self.giam_toi_da)
        return max(0, min(giam, so_tien_sau_ck))


class KhuyenMaiTienMat(KhuyenMai):
    def __init__(self, *args, so_tien_giam: int, **kw):
        super().__init__(*args, **kw)
        if so_tien_giam < 0:
            raise ValueError("so_tien_giam phải >= 0")
        self.so_tien_giam = so_tien_giam

    def tinh_giam(self, so_tien_sau_ck: int) -> int:
        return max(0, min(self.so_tien_giam, so_tien_sau_ck))
