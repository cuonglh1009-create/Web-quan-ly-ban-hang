import uuid
from abc import ABC
from datetime import datetime

from kho_ban_hang.domain.enums_chung import PhuongThucThanhToan, TrangThaiThanhToan


def moi_ma_gd() -> str:
    return "GD" + uuid.uuid4().hex[:12].upper()


class ThanhToan(ABC):
    phuong_thuc: PhuongThucThanhToan

    def __init__(self, ma_gd: str, don_hang, so_tien: int, thoi_diem: datetime,
                 trang_thai: TrangThaiThanhToan = TrangThaiThanhToan.THANH_CONG):
        self.ma_gd, self.don_hang, self.so_tien = ma_gd, don_hang, so_tien
        self.thoi_diem, self.trang_thai = thoi_diem, trang_thai


class ThanhToanTienMat(ThanhToan):
    phuong_thuc = PhuongThucThanhToan.TIEN_MAT

    def __init__(self, *args, tien_khach_dua: int, tien_thoi: int, **kw):
        super().__init__(*args, **kw)
        self.tien_khach_dua, self.tien_thoi = tien_khach_dua, tien_thoi


class ThanhToanChuyenKhoan(ThanhToan):
    phuong_thuc = PhuongThucThanhToan.CHUYEN_KHOAN

    def __init__(self, *args, ma_giao_dich_ngan_hang: str, ten_ngan_hang: str, **kw):
        super().__init__(*args, **kw)
        self.ma_giao_dich_ngan_hang, self.ten_ngan_hang = ma_giao_dich_ngan_hang, ten_ngan_hang
