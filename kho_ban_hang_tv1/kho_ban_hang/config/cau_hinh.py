from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class CauHinh:
    duong_dan_csdl: str
    nguong_ton_kho: int = 5
    so_ngay_canh_bao: int = 30
    ty_le_chiet_khau_thuong: Decimal = Decimal("0")
    ty_le_chiet_khau_vip: Decimal = Decimal("0.05")
    so_tien_moi_diem: int = 10000
    nguong_diem_vip: int = 1000
    thoi_han_phien_gio: int = 8
