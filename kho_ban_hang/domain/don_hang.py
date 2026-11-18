from datetime import date
from decimal import Decimal, ROUND_FLOOR

from kho_ban_hang.domain.enums_chung import TrangThaiDonHang as TT
from kho_ban_hang.domain.errors_ban_hang import LoiDuLieu, XungDot
from kho_ban_hang.domain.khach_hang import KhachHang
from kho_ban_hang.domain.khuyen_mai import KhuyenMai
from kho_ban_hang.domain.nhan_vien import NhanVien
from kho_ban_hang.domain.san_pham import SanPham


class ChiTietDonHang:
    def __init__(self, san_pham: SanPham, so_luong: int, don_gia: int):
        self.san_pham, self.so_luong, self.don_gia = san_pham, so_luong, don_gia

    def thanh_tien(self) -> int:
        return self.so_luong * self.don_gia


class DonHang:
    def __init__(self, ma_don: str, ngay_lap: date, trang_thai: TT, nhan_vien: NhanVien,
                 khach_hang: KhachHang | None = None,
                 chi_tiet: list[ChiTietDonHang] | None = None,
                 khuyen_mai: KhuyenMai | None = None,
                 giam_hang_khach: int = 0, giam_khuyen_mai: int = 0):
        self.ma_don, self.ngay_lap, self.trang_thai = ma_don, ngay_lap, trang_thai
        self.nhan_vien, self.khach_hang = nhan_vien, khach_hang
        self.chi_tiet = chi_tiet if chi_tiet is not None else []
        self.khuyen_mai = khuyen_mai
        self.giam_hang_khach, self.giam_khuyen_mai = giam_hang_khach, giam_khuyen_mai

    #  lập đơn (trạng thái NHAP)
    def them_chi_tiet(self, san_pham: SanPham, so_luong: int) -> None:  # QT06
        if self.trang_thai != TT.NHAP:
            raise XungDot("DON_KHONG_SUA_DUOC", "Chỉ thêm dòng khi đơn đang ở trạng thái nháp")
        if isinstance(so_luong, bool) or not isinstance(so_luong, int) or so_luong <= 0:
            raise LoiDuLieu("SO_LUONG_KHONG_HOP_LE", "Số lượng phải là số nguyên dương", "so_luong")
        if not san_pham.co_the_ban():
            raise LoiDuLieu("SAN_PHAM_KHONG_BAN_DUOC",
                            f"Sản phẩm {san_pham.ma_sp} hiện không thể bán", "ma_sp")
        for ct in self.chi_tiet:                      # gộp dòng trùng mã, giữ giá đã chốt
            if ct.san_pham.ma_sp == san_pham.ma_sp:
                ct.so_luong += so_luong
                return
        self.chi_tiet.append(ChiTietDonHang(san_pham, so_luong, san_pham.gia_niem_yet))

    def tinh_tam_tinh(self) -> int:
        return sum(ct.thanh_tien() for ct in self.chi_tiet)

    def chot_chiet_khau_hang(self, cau_hinh) -> None:  # QT11
        if self.trang_thai != TT.NHAP:
            raise XungDot("DON_KHONG_SUA_DUOC", "Chiết khấu chỉ chốt khi lập đơn")
        if self.khach_hang is None:
            self.giam_hang_khach = 0
            return
        ty_le = self.khach_hang.tinh_chiet_khau(cau_hinh)
        self.giam_hang_khach = int((Decimal(self.tinh_tam_tinh()) * ty_le)
                                   .to_integral_value(ROUND_FLOOR))

    def xac_nhan_cho_thanh_toan(self) -> None:
        if self.trang_thai != TT.NHAP:
            raise XungDot("SAI_TRANG_THAI", "Đơn không ở trạng thái nháp")
        if not self.chi_tiet:
            raise LoiDuLieu("DONG_RONG", "Đơn phải có ít nhất một dòng", "dong")
        self.trang_thai = TT.CHO_THANH_TOAN

    #  khuyến mại
    def ap_dung_khuyen_mai(self, km: KhuyenMai, ngay: date) -> None:  # QT07
        if self.trang_thai != TT.CHO_THANH_TOAN:
            raise XungDot("SAI_TRANG_THAI", "Chỉ áp mã cho đơn đang chờ thanh toán")
        tam_tinh = self.tinh_tam_tinh()
        if not km.ap_dung_duoc(tam_tinh, ngay):
            # mã cũ được giữ nguyên khi mã mới không hợp lệ
            raise LoiDuLieu("KHUYEN_MAI_KHONG_HOP_LE",
                            "Mã khuyến mại không áp dụng được cho đơn này", "ma_km")
        self.khuyen_mai = km
        self.giam_khuyen_mai = km.tinh_giam(tam_tinh - self.giam_hang_khach)

    def so_phai_tra(self) -> int:
        return max(0, self.tinh_tam_tinh() - self.giam_hang_khach - self.giam_khuyen_mai)

    #  vòng đời
    def danh_dau_da_thanh_toan(self) -> None:
        if self.trang_thai != TT.CHO_THANH_TOAN:
            raise XungDot("SAI_TRANG_THAI", "Đơn không ở trạng thái chờ thanh toán")
        self.trang_thai = TT.DA_THANH_TOAN

    def huy(self) -> None:
        if self.trang_thai == TT.DA_THANH_TOAN:
            raise XungDot("DON_DA_THANH_TOAN", "Đơn đã thanh toán, không thể hủy")
        if self.trang_thai != TT.CHO_THANH_TOAN:
            raise XungDot("SAI_TRANG_THAI", "Chỉ hủy được đơn đang chờ thanh toán")
        self.trang_thai = TT.DA_HUY
