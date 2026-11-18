from werkzeug.security import check_password_hash

from kho_ban_hang.domain.enums_chung import TrangThaiNhanVien, VaiTro


class NhanVien:
    def __init__(self, ma_nv: str, ho_ten: str, vai_tro: VaiTro, ten_dang_nhap: str,
                 mat_khau_hash: str,
                 trang_thai: TrangThaiNhanVien = TrangThaiNhanVien.HOAT_DONG):
        self.ma_nv, self.ho_ten, self.vai_tro = ma_nv, ho_ten, vai_tro
        self.ten_dang_nhap, self.mat_khau_hash, self.trang_thai = ten_dang_nhap, mat_khau_hash, trang_thai

    @property
    def dang_hoat_dong(self) -> bool:
        return self.trang_thai == TrangThaiNhanVien.HOAT_DONG

    def kiem_tra_mat_khau(self, mat_khau: str) -> bool:
        return check_password_hash(self.mat_khau_hash, mat_khau)

    def co_vai_tro(self, vai_tro: VaiTro) -> bool:
        return self.vai_tro == vai_tro
