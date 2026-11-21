from abc import ABC, abstractmethod

from ..domain.san_pham import SanPham


class ITraCuuSanPham(ABC):
    @abstractmethod
    def tim_theo_ma(self, ma_sp: str) -> SanPham: ...

    def tim_tat_ca(self) -> list[SanPham]:
        """Khả năng đọc danh mục cho UI; adapter dùng UI phải hiện thực phương thức này."""
        raise NotImplementedError("Adapter chưa hỗ trợ đọc danh mục sản phẩm")

    def lay_nha_cung_cap_theo_san_pham(self) -> dict[str, str]:
        """Nguồn cung từ phiếu đã xác nhận; adapter không có chứng từ trả map rỗng."""
        return {}

    def tim_nhieu(self, cac_ma) -> dict[str, SanPham]:
        return {ma: self.tim_theo_ma(ma) for ma in dict.fromkeys(cac_ma)}
