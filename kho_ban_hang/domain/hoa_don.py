from dataclasses import dataclass
from datetime import date

from .don_hang import DonHang
from .thanh_toan import ThanhToan
from .errors_ban_hang import LoiDuLieu


@dataclass(frozen=True)
class HoaDon:
    """Số tiền đã chốt không thể bị gán lại sau khi tạo hóa đơn."""
    ma_hd: str
    don_hang: DonHang
    thanh_toan: ThanhToan
    ngay_xuat: date
    tong_tien_truoc_giam: int
    tong_giam: int
    tong_thanh_toan: int

    def __post_init__(self):
        for field in ("tong_tien_truoc_giam", "tong_giam", "tong_thanh_toan"):
            value = getattr(self, field)
            if type(value) is not int or value < 0:
                raise LoiDuLieu("TIEN_HOA_DON_KHONG_HOP_LE", "Tiền hóa đơn phải là số nguyên không âm", field)
        if self.tong_giam > self.tong_tien_truoc_giam or self.tong_thanh_toan != self.tong_tien_truoc_giam-self.tong_giam:
            raise LoiDuLieu("TONG_HOA_DON_KHONG_KHOP", "Tổng thanh toán không khớp tiền hàng và tổng giảm", "tong_thanh_toan")

    @classmethod
    def tu_don_hang(cls, don, thanh_toan, ngay: date) -> "HoaDon":
        """Chốt số liệu tại thời điểm xuất; một hóa đơn mỗi đơn nên mã suy ra từ mã đơn."""
        return cls("HD-" + don.ma_don, don, thanh_toan, ngay,
                   don.tinh_tam_tinh(), don.giam_hang_khach + don.giam_khuyen_mai,
                   don.so_phai_tra())
