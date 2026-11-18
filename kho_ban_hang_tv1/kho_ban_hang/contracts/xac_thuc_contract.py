from abc import ABC, abstractmethod

from ..domain.enums_chung import VaiTro
from ..domain.nhan_vien import NhanVien


class IXacThuc(ABC):
    @abstractmethod
    def yeu_cau_vai_tro(
        self, ma_phien_web: str | None, *vai_tro_cho_phep: VaiTro
    ) -> NhanVien: ...
