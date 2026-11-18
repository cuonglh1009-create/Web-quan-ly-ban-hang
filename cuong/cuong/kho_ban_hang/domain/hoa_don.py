from datetime import date


class HoaDon:
    def __init__(self, ma_hd: str, don_hang, thanh_toan, ngay_xuat: date,
                 tong_tien_truoc_giam: int, tong_giam: int, tong_thanh_toan: int):
        self.ma_hd, self.don_hang, self.thanh_toan, self.ngay_xuat = ma_hd, don_hang, thanh_toan, ngay_xuat
        self.tong_tien_truoc_giam, self.tong_giam, self.tong_thanh_toan = (
            tong_tien_truoc_giam, tong_giam, tong_thanh_toan)

    @classmethod
    def tu_don_hang(cls, don, thanh_toan, ngay: date) -> "HoaDon":
        """Chốt số liệu tại thời điểm xuất; một hóa đơn mỗi đơn nên mã suy ra từ mã đơn."""
        return cls("HD-" + don.ma_don, don, thanh_toan, ngay,
                   don.tinh_tam_tinh(), don.giam_hang_khach + don.giam_khuyen_mai,
                   don.so_phai_tra())
