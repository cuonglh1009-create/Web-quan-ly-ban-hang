from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal

from .danh_muc import DanhMuc
from .enums_kho import LoaiSanPham, TrangThaiSanPham
from .errors import DuLieuKhongHopLeError


@dataclass(frozen=True)
class SanPham(ABC):
    ma_sp: str
    ten_sp: str
    gia_niem_yet: int
    don_vi_tinh: str
    trang_thai: TrangThaiSanPham
    danh_muc: DanhMuc

    @property
    @abstractmethod
    def loai(self) -> LoaiSanPham: ...

    def co_the_ban(self) -> bool:
        return self.trang_thai == TrangThaiSanPham.KINH_DOANH

    @property
    def can_ngay_lo(self) -> bool:
        return False

    def __post_init__(self):
        self._kiem_tra_gia(self.gia_niem_yet)

    def cap_nhat_gia(self, gia_moi: int) -> None:
        self._kiem_tra_gia(gia_moi)
        object.__setattr__(self, "gia_niem_yet", gia_moi)

    @staticmethod
    def _kiem_tra_gia(gia_moi):
        if type(gia_moi) is not int or gia_moi <= 0:
            raise DuLieuKhongHopLeError("Giá niêm yết phải là số nguyên dương.")


@dataclass(frozen=True)
class HangDienTu(SanPham):
    thoi_gian_bao_hanh: int
    cong_suat: Decimal
    loai = LoaiSanPham.DIEN_TU


@dataclass(frozen=True)
class HangThucPham(SanPham):
    yeu_cau_bao_quan: str
    loai = LoaiSanPham.THUC_PHAM

    @property
    def can_ngay_lo(self) -> bool:
        return True


@dataclass(frozen=True)
class HangThoiTrang(SanPham):
    kich_co: str
    chat_lieu: str
    loai = LoaiSanPham.THOI_TRANG
