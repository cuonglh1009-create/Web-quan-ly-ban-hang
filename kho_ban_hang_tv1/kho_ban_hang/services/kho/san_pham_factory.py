from decimal import Decimal

from ...domain.enums_kho import LoaiSanPham
from ...domain.san_pham import HangDienTu, HangThoiTrang, HangThucPham, SanPham


class SanPhamFactory:
    @staticmethod
    def tao_san_pham(loai: LoaiSanPham, du_lieu: dict) -> SanPham:
        if loai == LoaiSanPham.DIEN_TU:
            thuoc_tinh = {**du_lieu, "cong_suat": Decimal(str(du_lieu["cong_suat"]))}
            return HangDienTu(**thuoc_tinh)
        if loai == LoaiSanPham.THUC_PHAM:
            return HangThucPham(**du_lieu)
        return HangThoiTrang(**du_lieu)
