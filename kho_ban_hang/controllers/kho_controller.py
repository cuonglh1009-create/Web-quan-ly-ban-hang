from datetime import date

from ..contracts.kho_dto import BoLocLoDTO, DongNhapDTO, PhieuNhapDTO, PhieuNhapKetQuaDTO
from ..contracts.xac_thuc_contract import IXacThuc
from ..repositories.kho.kho_truy_van_repository import KhoTruyVanRepository
from ..domain.enums_chung import VaiTro


class KhoController:
    def __init__(self, xac_thuc: IXacThuc, thanh_phan_kho):
        self.xac_thuc = xac_thuc
        self.thanh_phan_kho = thanh_phan_kho
        self.nhap_kho = thanh_phan_kho.nhap_kho
        self.kho = thanh_phan_kho.kho

    def yeu_cau_nhan_vien_kho(self, ma_phien_web: str | None):
        return self.xac_thuc.yeu_cau_vai_tro(ma_phien_web, VaiTro.NV_KHO)

    def du_lieu_giao_dien(self, ma_phien_web):
        self.yeu_cau_nhan_vien_kho(ma_phien_web)
        repo = KhoTruyVanRepository(self.kho.ket_noi_db)
        return {
            "san_pham": repo.san_pham(),
            "nha_cung_cap": repo.nha_cung_cap(),
            "nha_cung_cap_theo_lo": repo.nha_cung_cap_theo_lo(),
            "so_ngay_canh_bao": self.kho.cau_hinh.so_ngay_canh_bao,
        }

    def danh_sach_phieu(self, ma_phien_web, q="", trang_thai=""):
        self.yeu_cau_nhan_vien_kho(ma_phien_web)
        return KhoTruyVanRepository(self.kho.ket_noi_db).phieu_nhap(q, trang_thai)

    def lap_phieu_nhap(self, ma_phien_web: str | None, du_lieu: PhieuNhapDTO) -> PhieuNhapKetQuaDTO:
        nhan_vien = self.yeu_cau_nhan_vien_kho(ma_phien_web)
        return self._ket_qua(self.nhap_kho.lap_phieu(du_lieu, nhan_vien))

    def tra_cuu_phieu_nhap(self, ma_phien_web: str | None, ma_phieu: str) -> PhieuNhapKetQuaDTO:
        self.yeu_cau_nhan_vien_kho(ma_phien_web)
        return self._ket_qua(self.nhap_kho.tra_cuu_phieu(ma_phieu))

    def xac_nhan_phieu_nhap(self, ma_phien_web: str | None, ma_phieu: str) -> PhieuNhapKetQuaDTO:
        self.yeu_cau_nhan_vien_kho(ma_phien_web)
        return self._ket_qua(self.nhap_kho.xac_nhan_phieu(ma_phieu, date.today()))

    def theo_doi_lo_hang(self, ma_phien_web: str | None, bo_loc: BoLocLoDTO):
        self.yeu_cau_nhan_vien_kho(ma_phien_web)
        return self.kho.tra_cuu_lo_hang(bo_loc)

    def xem_canh_bao_ton_kho(self, ma_phien_web: str | None):
        self.yeu_cau_nhan_vien_kho(ma_phien_web)
        return self.kho.xem_canh_bao()

    @staticmethod
    def _ket_qua(phieu) -> PhieuNhapKetQuaDTO:
        dong = [
            DongNhapDTO(
                ct.san_pham.ma_sp, ct.lo_hang.ma_lo, ct.so_luong_nhap,
                ct.gia_nhap, ct.lo_hang.ngay_san_xuat, ct.lo_hang.han_su_dung,
            )
            for ct in phieu.chi_tiet
        ]
        return PhieuNhapKetQuaDTO(
            phieu.ma_phieu, phieu.nha_cung_cap.ma_ncc, phieu.nguoi_lap.ma_nv,
            phieu.ngay_nhap, phieu.trang_thai, dong,
        )
