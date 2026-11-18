from kho_ban_hang.contracts.ban_hang_dto import DuLieuLapDonDTO
from kho_ban_hang.contracts.thanh_toan_contract import ThongTinThanhToanDTO
from kho_ban_hang.controllers.phan_hoi import PhanHoi
from kho_ban_hang.domain.enums_chung import VaiTro


class BanHangController:
    """Mỗi hàm nhận thêm ma_phien_web (so với đặc tả) vì cần lấy NhanVien từ phiên."""

    def __init__(self, xac_thuc, ban_hang, thanh_toan_service):
        self.xac_thuc, self.ban_hang, self.thanh_toan_service = xac_thuc, ban_hang, thanh_toan_service

    def _nv(self, ma_phien_web):
        return self.xac_thuc.yeu_cau_vai_tro(ma_phien_web, VaiTro.NV_BAN_HANG)

    def lap_don_va_giu_hang(self, ma_phien_web, du_lieu: dict) -> PhanHoi:
        nv = self._nv(ma_phien_web)
        kq = self.ban_hang.tao_don_va_giu_hang(DuLieuLapDonDTO.tu_json(du_lieu), nv)
        return PhanHoi(kq.to_dict(), 201)

    def tra_cuu_don(self, ma_phien_web, ma_don) -> PhanHoi:
        return PhanHoi(self.ban_hang.tra_cuu_don(ma_don, self._nv(ma_phien_web)).to_dict())

    def ap_dung_khuyen_mai(self, ma_phien_web, ma_don, du_lieu: dict) -> PhanHoi:
        nv = self._nv(ma_phien_web)
        return PhanHoi(self.ban_hang.ap_dung_khuyen_mai(ma_don, du_lieu.get("ma_km"), nv).to_dict())

    def thanh_toan_va_xuat_hoa_don(self, ma_phien_web, ma_don, du_lieu: dict) -> PhanHoi:
        nv = self._nv(ma_phien_web)
        tt = ThongTinThanhToanDTO.tu_json(du_lieu.get("phuong_thuc"), du_lieu.get("thong_tin"))
        return PhanHoi(self.thanh_toan_service.thanh_toan(ma_don, tt, nv).to_dict())

    def tra_cuu_hoa_don(self, ma_phien_web, ma_don) -> PhanHoi:
        nv = self._nv(ma_phien_web)
        return PhanHoi(self.thanh_toan_service.tra_cuu_hoa_don(ma_don, nv).to_dict())

    def huy_don(self, ma_phien_web, ma_don) -> PhanHoi:
        return PhanHoi(self.ban_hang.huy_don(ma_don, self._nv(ma_phien_web)).to_dict())
