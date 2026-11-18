from dataclasses import dataclass

from ...config.cau_hinh import CauHinh
from ...repositories.kho.danh_muc_repository import DanhMucRepository
from ...repositories.kho.giu_hang_repository import GiuHangRepository
from ...repositories.kho.lo_hang_repository import LoHangRepository
from ...repositories.kho.nha_cung_cap_repository import NhaCungCapRepository
from ...repositories.kho.phieu_nhap_repository import PhieuNhapRepository
from ...repositories.kho.san_pham_repository import SanPhamRepository
from .kho_service import KhoService
from .nhap_kho_service import NhapKhoService


@dataclass(frozen=True)
class ThanhPhanKho:
    san_pham_repo: SanPhamRepository
    nha_cung_cap_repo: NhaCungCapRepository
    kho: KhoService
    nhap_kho: NhapKhoService


def dang_ky_kho(ket_noi_db, cau_hinh: CauHinh, tim_nhan_vien) -> ThanhPhanKho:
    danh_muc = DanhMucRepository(ket_noi_db)
    san_pham = SanPhamRepository(ket_noi_db, danh_muc)
    ncc = NhaCungCapRepository(ket_noi_db)
    lo_hang = LoHangRepository(ket_noi_db, san_pham)
    giu_hang = GiuHangRepository(ket_noi_db, lo_hang)
    phieu_nhap = PhieuNhapRepository(ket_noi_db, san_pham, ncc, tim_nhan_vien)
    kho = KhoService(ket_noi_db, san_pham, lo_hang, giu_hang, cau_hinh)
    nhap_kho = NhapKhoService(ket_noi_db, phieu_nhap, san_pham, ncc, lo_hang)
    return ThanhPhanKho(san_pham, ncc, kho, nhap_kho)
