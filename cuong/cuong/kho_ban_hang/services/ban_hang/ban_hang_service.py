from datetime import date

from kho_ban_hang.contracts.ban_hang_dto import (DuLieuLapDonDTO, KetQuaHuyDonDTO, KetQuaLapDonDTO)
from kho_ban_hang.repositories.giao_dich import GiaoDich
from kho_ban_hang.contracts.kho_contract import ChiTietDatHangDTO
from kho_ban_hang.domain.don_hang import DonHang
from kho_ban_hang.domain.enums_chung import TrangThaiDonHang as TT
from kho_ban_hang.domain.errors import KhongTimThayError
from kho_ban_hang.domain.errors_ban_hang import KhongCoQuyen, KhongTimThay, LoiDuLieu, LoiNghiepVu, XungDot


def kiem_tra_quyen_tren_don(don: DonHang, nhan_vien) -> None:
    if don.nhan_vien.ma_nv != nhan_vien.ma_nv:
        raise KhongCoQuyen("KHONG_PHAI_DON_CUA_BAN", "Bạn không phải người lập đơn này")


class BanHangService:
    def __init__(self, kho, tra_cuu_san_pham, don_repo, khach_repo, km_repo, ket_noi, cau_hinh,
                 hom_nay=date.today):
        self.kho, self.tra_cuu, self.don_repo = kho, tra_cuu_san_pham, don_repo
        self.khach_repo, self.km_repo, self.db, self.cau_hinh = khach_repo, km_repo, ket_noi, cau_hinh
        self.hom_nay = hom_nay

    kiem_tra_quyen_tren_don = staticmethod(kiem_tra_quyen_tren_don)

    def _lay_don(self, ma_don, nhan_vien) -> DonHang:
        don = self.don_repo.tim_theo_ma(ma_don)
        if don is None:
            raise KhongTimThay("KHONG_TIM_THAY_DON", f"Không có đơn {ma_don}")
        kiem_tra_quyen_tren_don(don, nhan_vien)
        return don

    def tao_don_va_giu_hang(self, du_lieu: DuLieuLapDonDTO, nhan_vien) -> KetQuaLapDonDTO:
        with GiaoDich(self.db):   # lỗi ở bất kỳ bước nào: rollback cả đơn lẫn bản giữ
            khach = None
            if du_lieu.ma_kh:
                khach = self.khach_repo.tim_theo_ma(du_lieu.ma_kh)
                if khach is None:
                    raise LoiDuLieu("KHACH_KHONG_TON_TAI", "Không có khách hàng này", "ma_kh")
            don = DonHang(self.don_repo.cap_ma_moi(), self.hom_nay(), TT.NHAP, nhan_vien, khach)
            for i, d in enumerate(du_lieu.dong):
                try:
                    sp = self.tra_cuu.tim_theo_ma(d.ma_sp)
                except KhongTimThayError:
                    raise LoiDuLieu("SAN_PHAM_KHONG_TON_TAI", f"Không có sản phẩm {d.ma_sp}",
                                    f"dong[{i}].ma_sp")
                try:
                    don.them_chi_tiet(sp, d.so_luong)   # gộp mã trùng, chốt đơn giá
                except LoiNghiepVu as e:   # miền chỉ biết tên trường; service gắn số dòng
                    e.truong = f"dong[{i}].{e.truong or 'ma_sp'}"
                    raise
            don.chot_chiet_khau_hang(self.cau_hinh)
            don.xac_nhan_cho_thanh_toan()
            self.don_repo.luu(don)   # ghi đơn trước: giu_hang của Kho có khóa ngoại tới don_hang
            self.kho.giu_hang(don.ma_don, [ChiTietDatHangDTO(c.san_pham.ma_sp, c.so_luong)
                                           for c in don.chi_tiet])   # đã gộp mã trùng
        return KetQuaLapDonDTO.tu_don_hang(don)

    def tra_cuu_don(self, ma_don, nhan_vien) -> KetQuaLapDonDTO:
        return KetQuaLapDonDTO.tu_don_hang(self._lay_don(ma_don, nhan_vien))

    def ap_dung_khuyen_mai(self, ma_don, ma_km, nhan_vien) -> KetQuaLapDonDTO:
        if not isinstance(ma_km, str) or not ma_km.strip():
            raise LoiDuLieu("TRUONG_BAT_BUOC", "Nhập mã khuyến mại", "ma_km")
        with GiaoDich(self.db):
            don = self._lay_don(ma_don, nhan_vien)
            km = self.km_repo.tim_theo_ma(ma_km.strip())
            if km is None:
                raise LoiDuLieu("KHUYEN_MAI_KHONG_TON_TAI", "Mã khuyến mại không tồn tại", "ma_km")
            don.ap_dung_khuyen_mai(km, self.hom_nay())
            self.don_repo.luu(don)
        return KetQuaLapDonDTO.tu_don_hang(don)

    def huy_don(self, ma_don, nhan_vien) -> KetQuaHuyDonDTO:
        with GiaoDich(self.db):
            don = self._lay_don(ma_don, nhan_vien)
            if don.trang_thai == TT.DA_HUY:                 # hủy lặp: trả trạng thái cũ
                return KetQuaHuyDonDTO(don.ma_don, don.trang_thai.value)
            if don.trang_thai == TT.DA_THANH_TOAN:
                raise XungDot("DON_DA_THANH_TOAN", "Đơn đã thanh toán, không thể hủy")
            self.kho.hoan_giu_hang(don.ma_don)
            don.huy()
            self.don_repo.luu(don)
        return KetQuaHuyDonDTO(don.ma_don, don.trang_thai.value)
