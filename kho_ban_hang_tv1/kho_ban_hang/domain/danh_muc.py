from dataclasses import dataclass

from .enums_kho import TrangThaiDanhMuc


@dataclass
class DanhMuc:
    ma_dm: str
    ten_dm: str
    mo_ta: str
    trang_thai: TrangThaiDanhMuc
