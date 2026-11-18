from enum import Enum


class VaiTro(str, Enum):
    NV_KHO = "NV_KHO"
    NV_BAN_HANG = "NV_BAN_HANG"


class TrangThaiNhanVien(str, Enum):
    HOAT_DONG = "HOAT_DONG"
    NGUNG_HOAT_DONG = "NGUNG_HOAT_DONG"


class TrangThaiDonHang(str, Enum):
    NHAP = "NHAP"
    CHO_THANH_TOAN = "CHO_THANH_TOAN"
    DA_THANH_TOAN = "DA_THANH_TOAN"
    DA_HUY = "DA_HUY"


class TrangThaiKhuyenMai(str, Enum):
    HOAT_DONG = "HOAT_DONG"
    NGUNG = "NGUNG"


class TrangThaiThanhToan(str, Enum):
    THANH_CONG = "THANH_CONG"
    THAT_BAI = "THAT_BAI"


class PhuongThucThanhToan(str, Enum):
    TIEN_MAT = "TIEN_MAT"
    CHUYEN_KHOAN = "CHUYEN_KHOAN"
