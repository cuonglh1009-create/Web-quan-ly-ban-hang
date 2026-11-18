from abc import ABC, abstractmethod

from ..domain.san_pham import SanPham


class ITraCuuSanPham(ABC):
    @abstractmethod
    def tim_theo_ma(self, ma_sp: str) -> SanPham: ...
