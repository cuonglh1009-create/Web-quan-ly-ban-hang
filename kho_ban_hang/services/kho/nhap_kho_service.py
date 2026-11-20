from datetime import date

from ...contracts.kho_dto import PhieuNhapDTO
from ...domain.enums_kho import TrangThaiPhieuNhap
from ...domain.errors import KhongTimThayError
from ...domain.errors_kho import TrungMaLoError
from ...domain.lo_hang import LoHang
from ...domain.nhan_vien import NhanVien
from ...domain.phieu_nhap import ChiTietPhieuNhap, PhieuNhapKho
from ...repositories.giao_dich import GiaoDich


class NhapKhoService:
    def __init__(self, ket_noi_db, phieu_nhap_repo, san_pham_repo, nha_cung_cap_repo, lo_hang_repo):
        self.ket_noi_db = ket_noi_db
        self.phieu_nhap_repo = phieu_nhap_repo
        self.san_pham_repo = san_pham_repo
        self.nha_cung_cap_repo = nha_cung_cap_repo
        self.lo_hang_repo = lo_hang_repo

    def lap_phieu(self, du_lieu: PhieuNhapDTO, nguoi_lap: NhanVien) -> PhieuNhapKho:
        with GiaoDich(self.ket_noi_db):
            phieu = PhieuNhapKho(
                self.phieu_nhap_repo.cap_ma_moi(), du_lieu.ngay_nhap, nguoi_lap,
                self.nha_cung_cap_repo.tim_theo_ma(du_lieu.ma_ncc),
            )
            san_pham = self.san_pham_repo.tim_nhieu(dong.ma_sp for dong in du_lieu.dong)
            ma_lo_da_doc = set()
            for i, dong in enumerate(du_lieu.dong):
                if dong.ma_lo in ma_lo_da_doc:
                    raise TrungMaLoError("Mã lô bị lặp trong phiếu.", f"dong[{i}].ma_lo")
                ma_lo_da_doc.add(dong.ma_lo)
                sp = san_pham.get(dong.ma_sp)
                if sp is None:
                    raise KhongTimThayError(f"Không tìm thấy sản phẩm {dong.ma_sp}.", f"dong[{i}].ma_sp")
                lo = LoHang(
                    dong.ma_lo, sp, du_lieu.ngay_nhap, dong.ngay_san_xuat,
                    dong.han_su_dung, dong.so_luong_nhap, dong.gia_nhap,
                )
                phieu.them_chi_tiet(ChiTietPhieuNhap(sp, dong.so_luong_nhap, dong.gia_nhap, lo))
            phieu.kiem_tra_truoc_xac_nhan(date.today())
            self.phieu_nhap_repo.luu(phieu)
        return phieu

    def tra_cuu_phieu(self, ma_phieu: str) -> PhieuNhapKho:
        return self.phieu_nhap_repo.tim_theo_ma(ma_phieu)

    def xac_nhan_phieu(self, ma_phieu: str, ngay_xac_nhan: date) -> PhieuNhapKho:
        with GiaoDich(self.ket_noi_db):
            phieu = self.phieu_nhap_repo.tim_theo_ma(ma_phieu)
            if phieu.trang_thai == TrangThaiPhieuNhap.DA_XAC_NHAN:
                return phieu
            cac_lo = phieu.xac_nhan(ngay_xac_nhan)
            for i, lo in enumerate(cac_lo):
                if self.lo_hang_repo.ton_tai_ma_lo(lo.ma_lo):
                    raise TrungMaLoError(f"Mã lô {lo.ma_lo} đã có trong kho.", f"dong[{i}].ma_lo")
            for lo in cac_lo:
                self.lo_hang_repo.them(lo)
            self.phieu_nhap_repo.cap_nhat_trang_thai(phieu)
        return phieu
