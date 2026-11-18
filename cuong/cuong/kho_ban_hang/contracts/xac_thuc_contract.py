from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from kho_ban_hang.domain.enums_chung import VaiTro
from kho_ban_hang.domain.nhan_vien import NhanVien


@dataclass
class PhienLamViec:
    ma_bam: str                      # băm của mã phiên ngẫu nhiên trong cookie
    ma_nv: str | None
    thoi_diem_dang_nhap: datetime | None
    het_han_luc: datetime
    csrf_token: str

    @property
    def da_xac_thuc(self) -> bool:
        return self.ma_nv is not None

    def het_han(self, bay_gio: datetime) -> bool:
        return self.het_han_luc <= bay_gio


@dataclass
class PhienHienTai:
    """Kết quả lay_phien. ma_phien_web_moi khác None khi vừa cấp phiên ẩn danh mới
    và controller phải đặt cookie."""
    phien: PhienLamViec
    nhan_vien: NhanVien | None
    ma_phien_web_moi: str | None = None


class IXacThuc(ABC):
    @abstractmethod
    def yeu_cau_vai_tro(self, ma_phien_web: str | None, *vai_tro_cho_phep: VaiTro) -> NhanVien:
        """Thiếu phiên hợp lệ: ChuaDangNhap (401). Sai vai trò: KhongCoQuyen (403)."""
