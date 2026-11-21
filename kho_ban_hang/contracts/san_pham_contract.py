from abc import ABC, abstractmethod

from ..domain.san_pham import SanPham


class ITraCuuSanPham(ABC):
    @abstractmethod
    def tim_theo_ma(self, ma_sp: str) -> SanPham: ...

    def tim_nhieu(self, cac_ma) -> dict[str, SanPham]:
        return {ma: self.tim_theo_ma(ma) for ma in dict.fromkeys(cac_ma)}
