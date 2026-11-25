from dataclasses import dataclass
from datetime import date

from .kho_contract import CanhBaoDTO
from ..domain.enums_kho import TrangThaiPhieuNhap


@dataclass(frozen=True)
class DongNhapDTO:
    ma_sp: str
    ma_lo: str
    so_luong_nhap: int
    gia_nhap: int
    ngay_san_xuat: date | None = None
    han_su_dung: date | None = None
    ten_sp: str | None = None


@dataclass(frozen=True)
class PhieuNhapDTO:
    ma_ncc: str
    ngay_nhap: date
    dong: list[DongNhapDTO]
    ten_ncc: str | None = None


@dataclass(frozen=True)
class PhieuNhapKetQuaDTO:
    ma_phieu: str
    ma_ncc: str
    ma_nv: str
    ngay_nhap: date
    trang_thai: TrangThaiPhieuNhap
    dong: list[DongNhapDTO]


@dataclass(frozen=True)
class BoLocLoDTO:
    ma_lo: str | None = None
    ma_sp: str | None = None


@dataclass(frozen=True)
class DongLoHangDTO:
    ma_lo: str
    ma_sp: str
    ngay_nhap: date
    ngay_san_xuat: date | None
    han_su_dung: date | None
    ton_thuc_te: int
    dang_giu: int
    kha_dung: int


@dataclass(frozen=True)
class KetQuaCanhBaoDTO:
    ton_thap: list[CanhBaoDTO]
    sap_het_han: list[CanhBaoDTO]
