from dataclasses import dataclass

from .enums_kho import TrangThaiNhaCungCap


@dataclass
class NhaCungCap:
    ma_ncc: str
    ten_ncc: str
    so_dien_thoai: str
    dia_chi: str
    trang_thai: TrangThaiNhaCungCap

    def dang_hoat_dong(self) -> bool:
        return self.trang_thai == TrangThaiNhaCungCap.HOAT_DONG
