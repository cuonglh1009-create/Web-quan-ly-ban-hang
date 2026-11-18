from .errors import (ChuaDangNhapError, CsrfKhongHopLeError, DuLieuKhongHopLeError,
                     KhongDuQuyenError, KhongTimThayError, NghiepVuError)


class LoiNghiepVu(NghiepVuError):
    def __init__(self, ma_loi: str, thong_bao: str, truong: str | None = None):
        NghiepVuError.__init__(self, thong_bao, truong)
        self.ma_loi = ma_loi


class LoiDuLieu(LoiNghiepVu, DuLieuKhongHopLeError):        # 400
    pass


class ChuaDangNhap(LoiNghiepVu, ChuaDangNhapError):         # 401
    pass


class KhongCoQuyen(LoiNghiepVu, KhongDuQuyenError):         # 403
    pass


class SaiCSRF(LoiNghiepVu, CsrfKhongHopLeError):            # 403
    pass


class KhongTimThay(LoiNghiepVu, KhongTimThayError):         # 404
    pass


class XungDot(LoiNghiepVu):
    status = 409


class QuaSoLanThu(LoiNghiepVu):
    status = 429
