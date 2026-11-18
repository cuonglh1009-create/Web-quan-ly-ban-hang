class NghiepVuError(Exception):
    ma_loi = "NGHIEP_VU"
    status = 400

    def __init__(self, thong_bao: str, truong: str | None = None):
        super().__init__(thong_bao)
        self.thong_bao = thong_bao
        self.truong = truong


class DuLieuKhongHopLeError(NghiepVuError):
    ma_loi = "DU_LIEU_KHONG_HOP_LE"


class KhongTimThayError(NghiepVuError):
    ma_loi = "KHONG_TIM_THAY"
    status = 404


class TrangThaiKhongHopLeError(NghiepVuError):
    ma_loi = "TRANG_THAI_KHONG_HOP_LE"
    status = 409


class ChuaDangNhapError(NghiepVuError):
    ma_loi = "CHUA_DANG_NHAP"
    status = 401


class KhongDuQuyenError(NghiepVuError):
    ma_loi = "KHONG_DU_QUYEN"
    status = 403


class CsrfKhongHopLeError(NghiepVuError):
    ma_loi = "CSRF_KHONG_HOP_LE"
    status = 403
