from dataclasses import dataclass

from .enums_chung import TrangThaiNhanVien, VaiTro


@dataclass(frozen=True)
class NhanVien:
    ma_nv: str
    ho_ten: str
    vai_tro: VaiTro
    ten_dang_nhap: str
    mat_khau_hash: str
    trang_thai: TrangThaiNhanVien

    def co_vai_tro(self, vai_tro: VaiTro) -> bool:
        return self.vai_tro == vai_tro
