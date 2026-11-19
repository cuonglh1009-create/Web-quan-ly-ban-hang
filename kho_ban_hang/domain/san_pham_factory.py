from abc import ABC, abstractmethod
from decimal import Decimal

from .enums_kho import LoaiSanPham
from .san_pham import HangDienTu, HangThoiTrang, HangThucPham, SanPham


class SanPhamFactory(ABC):
    @abstractmethod
    def tao(self, du_lieu: dict) -> SanPham: ...

    @staticmethod
    def tao_san_pham(loai: LoaiSanPham, du_lieu: dict) -> SanPham:
        return _FACTORIES[LoaiSanPham(loai)].tao(du_lieu)


class HangDienTuFactory(SanPhamFactory):
    def tao(self, du_lieu: dict) -> SanPham:
        return HangDienTu(**{**du_lieu, "cong_suat": Decimal(str(du_lieu["cong_suat"]))})


class HangThucPhamFactory(SanPhamFactory):
    def tao(self, du_lieu: dict) -> SanPham:
        return HangThucPham(**du_lieu)


class HangThoiTrangFactory(SanPhamFactory):
    def tao(self, du_lieu: dict) -> SanPham:
        return HangThoiTrang(**du_lieu)


_FACTORIES = {
    LoaiSanPham.DIEN_TU: HangDienTuFactory(),
    LoaiSanPham.THUC_PHAM: HangThucPhamFactory(),
    LoaiSanPham.THOI_TRANG: HangThoiTrangFactory(),
}
