from datetime import date

from kho_ban_hang.contracts.ban_hang_dto import HoaDonDTO, KetQuaThanhToanDTO
from kho_ban_hang.repositories.giao_dich import GiaoDich
from kho_ban_hang.contracts.thanh_toan_contract import ThongTinThanhToanDTO
from kho_ban_hang.domain.enums_chung import PhuongThucThanhToan as PT
from kho_ban_hang.domain.enums_chung import TrangThaiDonHang as TT
from kho_ban_hang.domain.errors_ban_hang import KhongTimThay, XungDot
from kho_ban_hang.domain.hoa_don import HoaDon
from kho_ban_hang.domain.thanh_toan import ThanhToanTienMat
from kho_ban_hang.services.ban_hang.ban_hang_service import kiem_tra_quyen_tren_don


class ThanhToanService:
    def __init__(self, kho, don_repo, khach_repo, thanh_toan_repo, hoa_don_repo, ket_noi,
                 strategies: dict, cau_hinh, hom_nay=date.today):
        self.kho, self.don_repo, self.khach_repo = kho, don_repo, khach_repo
        self.tt_repo, self.hd_repo, self.db = thanh_toan_repo, hoa_don_repo, ket_noi
        self.strategies, self.cau_hinh, self.hom_nay = strategies, cau_hinh, hom_nay

    def _lay_don(self, ma_don, nhan_vien):
        don = self.don_repo.tim_theo_ma(ma_don)
        if don is None:
            raise KhongTimThay("KHONG_TIM_THAY_DON", f"Không có đơn {ma_don}")
        kiem_tra_quyen_tren_don(don, nhan_vien)      # kiểm tra chủ đơn trước mọi việc khác
        return don

    def thanh_toan(self, ma_don, thong_tin: ThongTinThanhToanDTO, nhan_vien) -> KetQuaThanhToanDTO:
        with GiaoDich(self.db):
            don = self._lay_don(ma_don, nhan_vien)   # đọc lại trong giao dịch
            if don.trang_thai == TT.DA_THANH_TOAN:   # thanh toán lặp: trả hóa đơn cũ
                hd = self.hd_repo.tim_theo_ma_don(ma_don)
                tien_thoi = getattr(hd.thanh_toan, "tien_thoi", None)
                return KetQuaThanhToanDTO(hd.ma_hd, hd.tong_thanh_toan, tien_thoi, True)
            if don.trang_thai != TT.CHO_THANH_TOAN:
                raise XungDot("SAI_TRANG_THAI", "Đơn không ở trạng thái chờ thanh toán")

            phai_tra = don.so_phai_tra()
            if phai_tra == 0:                        # đơn 0 đồng ghi nhận bằng tiền mặt
                thong_tin = ThongTinThanhToanDTO(PT.TIEN_MAT, tien_khach_dua=0)
            tt = self.strategies[thong_tin.phuong_thuc].xu_ly(don, thong_tin)
            if thong_tin.phuong_thuc == PT.CHUYEN_KHOAN and self.tt_repo.ton_tai_tham_chieu(
                    tt.ten_ngan_hang, tt.ma_giao_dich_ngan_hang):
                raise XungDot("THAM_CHIEU_TRUNG", "Mã giao dịch ngân hàng này đã được dùng",
                              "thong_tin.ma_giao_dich_ngan_hang")

            self.kho.xac_nhan_xuat_kho(don.ma_don)
            self.tt_repo.luu(tt)
            hd = HoaDon.tu_don_hang(don, tt, self.hom_nay())
            self.hd_repo.luu(hd)
            don.danh_dau_da_thanh_toan()
            self.don_repo.luu(don)
            if don.khach_hang is not None:           # QT10
                len_vip = don.khach_hang.cong_diem(phai_tra, self.cau_hinh)
                self.khach_repo.luu(don.khach_hang)
                if len_vip:
                    self.khach_repo.nang_hang_vip(don.khach_hang.ma_kh, self.hom_nay())
        tien_thoi = tt.tien_thoi if isinstance(tt, ThanhToanTienMat) else None
        return KetQuaThanhToanDTO(hd.ma_hd, phai_tra, tien_thoi, False)

    def tra_cuu_hoa_don(self, ma_don, nhan_vien) -> HoaDonDTO:
        don = self._lay_don(ma_don, nhan_vien)
        hd = self.hd_repo.tim_theo_ma_don(ma_don)
        if hd is None:
            raise KhongTimThay("CHUA_CO_HOA_DON", "Đơn này chưa có hóa đơn")
        tt = hd.thanh_toan
        return HoaDonDTO(
            hd.ma_hd, don.ma_don, hd.ngay_xuat.isoformat(), hd.tong_tien_truoc_giam,
            hd.tong_giam, hd.tong_thanh_toan, tt.phuong_thuc.value,
            getattr(tt, "tien_thoi", None),
            [{"ma_sp": c.san_pham.ma_sp, "ten_sp": c.san_pham.ten_sp,
              "don_vi_tinh": c.san_pham.don_vi_tinh, "so_luong": c.so_luong, "don_gia": c.don_gia,
              "thanh_tien": c.thanh_tien()} for c in don.chi_tiet])   # giá đã chốt
