from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from .errors_ban_hang import LoiDuLieu


class KhachHang(ABC):
    la_vip = False

    def __init__(self, ma_kh: str, ho_ten: str, so_dien_thoai: str, dia_chi: str,
                 diem_tich_luy: int = 0):
        self.ma_kh, self.ho_ten = ma_kh, ho_ten
        self.so_dien_thoai, self.dia_chi = so_dien_thoai, dia_chi
        if type(diem_tich_luy) is not int or diem_tich_luy < 0:
            raise LoiDuLieu("DIEM_KHONG_HOP_LE", "Điểm phải là số nguyên không âm", "diem_tich_luy")
        self._diem_tich_luy = diem_tich_luy

    @property
    def diem_tich_luy(self) -> int:
        return self._diem_tich_luy

    @abstractmethod
    def tinh_chiet_khau(self, cau_hinh) -> Decimal:
        """Trả TỶ LỆ (vd 0.05), không phải số tiền."""

    def cong_diem(self, so_tien_thuc_tra: int, cau_hinh) -> bool:
        """Cộng điểm theo số tiền thực trả. True nếu khách thường vừa đủ ngưỡng nâng VIP."""  # QT10
        if type(so_tien_thuc_tra) is not int or so_tien_thuc_tra < 0:
            raise LoiDuLieu("TIEN_TICH_DIEM_KHONG_HOP_LE", "Tiền tích điểm phải là số nguyên không âm", "so_tien_thuc_tra")
        if cau_hinh.so_tien_moi_diem > 0 and so_tien_thuc_tra > 0:
            self._diem_tich_luy += so_tien_thuc_tra // cau_hinh.so_tien_moi_diem
        return (not self.la_vip) and self.diem_tich_luy >= cau_hinh.nguong_diem_vip


class KhachThuong(KhachHang):
    def tinh_chiet_khau(self, cau_hinh) -> Decimal:
        return cau_hinh.ty_le_chiet_khau_thuong


class KhachVIP(KhachHang):
    la_vip = True

    def __init__(self, ma_kh, ho_ten, so_dien_thoai, dia_chi, diem_tich_luy=0,
                 ngay_len_hang: date | None = None):
        super().__init__(ma_kh, ho_ten, so_dien_thoai, dia_chi, diem_tich_luy)
        self.ngay_len_hang = ngay_len_hang

    def tinh_chiet_khau(self, cau_hinh) -> Decimal:
        return cau_hinh.ty_le_chiet_khau_vip
