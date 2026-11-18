from kho_ban_hang.controllers.phan_hoi import PhanHoi
from kho_ban_hang.domain.enums_chung import VaiTro
from kho_ban_hang.domain.errors_ban_hang import LoiDuLieu

TRANG_CHU = {VaiTro.NV_KHO: "/kho", VaiTro.NV_BAN_HANG: "/ban-hang"}


def trang_chu_cua(nhan_vien) -> str:
    return TRANG_CHU[nhan_vien.vai_tro]


def _cau_truc_phien(ph) -> dict:
    nv = ph.nhan_vien
    return {"da_dang_nhap": nv is not None,
            "nguoi_dung": None if nv is None else
            {"ma_nv": nv.ma_nv, "ho_ten": nv.ho_ten, "vai_tro": nv.vai_tro.value},
            "csrf_token": ph.phien.csrf_token}


class XacThucController:
    """Cookie và CSRF đã được lớp web kiểm tra trước (before_request); controller nhận mã
    phiên thô, gọi service rồi báo lớp web đặt hoặc xóa cookie."""

    def __init__(self, xac_thuc):
        self.xac_thuc = xac_thuc

    def lay_phien(self, ma_phien_web) -> PhanHoi:
        ph = self.xac_thuc.lay_phien(ma_phien_web)
        return PhanHoi(_cau_truc_phien(ph), 200, dat_cookie=ph.ma_phien_web_moi)

    def dang_nhap(self, ma_phien_web, du_lieu: dict) -> PhanHoi:
        ph = self.xac_thuc.dang_nhap(du_lieu.get("ten_dang_nhap"), du_lieu.get("mat_khau"),
                                     ma_phien_web)
        kq = _cau_truc_phien(ph)
        kq["trang_chu"] = trang_chu_cua(ph.nhan_vien)
        return PhanHoi(kq, 200, dat_cookie=ph.ma_phien_web_moi)

    def dang_xuat(self, ma_phien_web) -> PhanHoi:
        self.xac_thuc.dang_xuat(ma_phien_web)
        return PhanHoi({"trang_chu": "/dang-nhap"}, 200, xoa_cookie=True)
