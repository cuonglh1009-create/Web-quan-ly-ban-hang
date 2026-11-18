from dataclasses import dataclass
from datetime import date

from .errors import DuLieuKhongHopLeError
from .errors_kho import KhongDuTonKhoError
from .san_pham import SanPham


@dataclass
class LoHang:
    ma_lo: str
    san_pham: SanPham
    ngay_nhap: date
    ngay_san_xuat: date | None
    han_su_dung: date | None
    so_luong_con_lai: int
    gia_nhap: int

    def con_han_su_dung(self, ngay: date) -> bool:
        return self.han_su_dung is None or ngay <= self.han_su_dung

    def so_ngay_den_han(self, ngay: date) -> int | None:
        if self.han_su_dung is None:
            return None
        return (self.han_su_dung - ngay).days

    def giam_ton(self, so_luong: int) -> None:
        if type(so_luong) is not int or so_luong <= 0:
            raise DuLieuKhongHopLeError("Lượng xuất phải là số nguyên dương.")
        if so_luong > self.so_luong_con_lai:
            raise KhongDuTonKhoError(f"Lô {self.ma_lo} thiếu tồn thực tế.")
        self.so_luong_con_lai -= so_luong


@dataclass(frozen=True)
class GiuHang:
    ma_don: str
    lo_hang: LoHang
    so_luong: int

    def khoa(self) -> tuple[str, str]:
        return self.ma_don, self.lo_hang.ma_lo
