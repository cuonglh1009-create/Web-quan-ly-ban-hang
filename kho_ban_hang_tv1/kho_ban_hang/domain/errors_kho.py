from .errors import NghiepVuError


class KhongDuTonKhoError(NghiepVuError):
    ma_loi = "KHONG_DU_TON_KHO"
    status = 409


class TrungMaLoError(NghiepVuError):
    ma_loi = "TRUNG_MA_LO"
    status = 409


class HetHanSuDungError(NghiepVuError):
    ma_loi = "HET_HAN_SU_DUNG"
    status = 409
