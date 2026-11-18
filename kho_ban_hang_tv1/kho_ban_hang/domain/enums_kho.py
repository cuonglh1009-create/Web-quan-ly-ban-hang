from enum import StrEnum


class TrangThaiSanPham(StrEnum):
    KINH_DOANH = "KINH_DOANH"
    NGUNG_KINH_DOANH = "NGUNG_KINH_DOANH"


class TrangThaiDanhMuc(StrEnum):
    HOAT_DONG = "HOAT_DONG"
    NGUNG_HOAT_DONG = "NGUNG_HOAT_DONG"


class TrangThaiNhaCungCap(StrEnum):
    HOAT_DONG = "HOAT_DONG"
    NGUNG_HOAT_DONG = "NGUNG_HOAT_DONG"


class TrangThaiPhieuNhap(StrEnum):
    NHAP = "NHAP"
    DA_XAC_NHAN = "DA_XAC_NHAN"


class LoaiSanPham(StrEnum):
    DIEN_TU = "DIEN_TU"
    THUC_PHAM = "THUC_PHAM"
    THOI_TRANG = "THOI_TRANG"


class LoaiCanhBao(StrEnum):
    TON_THAP = "TON_THAP"
    SAP_HET_HAN = "SAP_HET_HAN"
