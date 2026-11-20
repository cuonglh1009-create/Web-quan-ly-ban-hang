from collections import Counter
from datetime import date

from ...contracts.kho_contract import CanhBaoDTO, ChiTietDatHangDTO, IKho, IKhoObserver
from ...contracts.kho_dto import BoLocLoDTO, DongLoHangDTO, KetQuaCanhBaoDTO
from ...domain.enums_kho import LoaiCanhBao
from ...domain.errors import DuLieuKhongHopLeError, TrangThaiKhongHopLeError, KhongTimThayError
from ...domain.errors_kho import HetHanSuDungError, KhongDuTonKhoError
from ...domain.lo_hang import GiuHang, LoHang
from .canh_bao_observer import CanhBaoSapHetHanObserver, CanhBaoTonThapObserver


class KhoService(IKho):
    def __init__(self, ket_noi_db, san_pham_repo, lo_hang_repo, giu_hang_repo, cau_hinh):
        self.ket_noi_db = ket_noi_db
        self.san_pham_repo = san_pham_repo
        self.lo_hang_repo = lo_hang_repo
        self.giu_hang_repo = giu_hang_repo
        self.cau_hinh = cau_hinh
        self.observers: list[IKhoObserver] = []

    def _yeu_cau_giao_dich(self):
        if not self.ket_noi_db.in_transaction:
            raise RuntimeError("Thao tác ghi IKho cần GiaoDich từ service gọi.")

    @staticmethod
    def _kha_dung(lo: LoHang, dang_giu: int, ngay: date) -> int:
        if lo.san_pham.co_the_ban() and lo.con_han_su_dung(ngay):
            return lo.so_luong_con_lai - dang_giu
        return 0

    def lay_so_luong_kha_dung(self, ma_sp: str) -> int:
        self.san_pham_repo.tim_theo_ma(ma_sp)
        return sum(dong.kha_dung for dong in self.tra_cuu_lo_hang(BoLocLoDTO(ma_sp=ma_sp)))

    def lay_so_luong_kha_dung_nhieu(self, ma_san_pham: list[str]) -> dict[str, int]:
        cac_ma = set(ma_san_pham)
        if not cac_ma:
            return {}
        da_co = self.san_pham_repo.tim_nhieu(cac_ma)
        for ma in sorted(cac_ma - da_co.keys()):
            raise KhongTimThayError(f"Không tìm thấy sản phẩm {ma}.", "ma_sp")
        ket_qua = dict.fromkeys(cac_ma, 0)
        # Dùng lại quy tắc khả dụng của Kho; không giữ cache qua giao dịch.
        for dong in self.tra_cuu_lo_hang(BoLocLoDTO()):
            if dong.ma_sp in ket_qua:
                ket_qua[dong.ma_sp] += dong.kha_dung
        return ket_qua

    def chon_lo_xuat(self, ma_sp: str, so_luong: int, ngay: date) -> list[tuple[LoHang, int]]:
        if type(so_luong) is not int or so_luong <= 0:
            raise DuLieuKhongHopLeError("Số lượng giữ phải là số nguyên dương.")
        self.san_pham_repo.tim_theo_ma(ma_sp)
        cac_lo = self.lo_hang_repo.tim_voi_so_dang_giu(None, ma_sp, uu_tien_xuat=True)
        phan_bo = []
        con_thieu = so_luong
        for lo, dang_giu in cac_lo:
            lay = min(self._kha_dung(lo, dang_giu, ngay), con_thieu)
            if lay > 0:
                phan_bo.append((lo, lay))
                con_thieu -= lay
            if con_thieu == 0:
                return phan_bo
        raise KhongDuTonKhoError(f"Sản phẩm {ma_sp} thiếu {con_thieu} đơn vị khả dụng.")

    def giu_hang(self, ma_don: str, chi_tiet: list[ChiTietDatHangDTO]) -> None:
        self._yeu_cau_giao_dich()
        if not chi_tiet:
            raise DuLieuKhongHopLeError("Cần ít nhất một dòng giữ hàng.")
        yeu_cau = Counter()
        for dong in chi_tiet:
            if type(dong.so_luong) is not int or dong.so_luong <= 0:
                raise DuLieuKhongHopLeError("Số lượng giữ phải là số nguyên dương.")
            yeu_cau[dong.ma_sp] += dong.so_luong
        da_giu = self.giu_hang_repo.tim_theo_don(ma_don)
        if da_giu:
            luong_da_giu = Counter()
            for giu in da_giu:
                luong_da_giu[giu.lo_hang.san_pham.ma_sp] += giu.so_luong
            if luong_da_giu == yeu_cau:
                return
            raise TrangThaiKhongHopLeError("Đơn đã có yêu cầu giữ hàng khác.")
        ngay = date.today()
        phan_bo = []
        for ma_sp, so_luong in yeu_cau.items():
            phan_bo.extend(GiuHang(ma_don, lo, luong) for lo, luong in self.chon_lo_xuat(ma_sp, so_luong, ngay))
        self.giu_hang_repo.luu_nhieu(phan_bo)

    def xac_nhan_xuat_kho(self, ma_don: str) -> None:
        self._yeu_cau_giao_dich()
        cac_luong_giu = self.giu_hang_repo.tim_theo_don(ma_don)
        if not cac_luong_giu:
            raise KhongDuTonKhoError(f"Đơn {ma_don} chưa có hàng được giữ.")
        ngay = date.today()
        for giu in cac_luong_giu:
            if not giu.lo_hang.con_han_su_dung(ngay):
                raise HetHanSuDungError(f"Lô {giu.lo_hang.ma_lo} đã hết hạn.")
            giu.lo_hang.giam_ton(giu.so_luong)
        for giu in cac_luong_giu:
            self.lo_hang_repo.luu(giu.lo_hang)
        self.giu_hang_repo.xoa_theo_don(ma_don)

    def hoan_giu_hang(self, ma_don: str) -> None:
        self._yeu_cau_giao_dich()
        self.giu_hang_repo.xoa_theo_don(ma_don)

    def tra_cuu_lo_hang(self, bo_loc: BoLocLoDTO, ngay: date | None = None) -> list[DongLoHangDTO]:
        ngay = ngay or date.today()
        ket_qua = []
        for lo, dang_giu in self.lo_hang_repo.tim_voi_so_dang_giu(bo_loc.ma_lo, bo_loc.ma_sp):
            ket_qua.append(DongLoHangDTO(
                lo.ma_lo, lo.san_pham.ma_sp, lo.ngay_nhap, lo.ngay_san_xuat, lo.han_su_dung,
                lo.so_luong_con_lai, dang_giu, self._kha_dung(lo, dang_giu, ngay),
            ))
        return ket_qua

    def dang_ky_observer(self, observer: IKhoObserver) -> None:
        self.observers.append(observer)

    def _phat_canh_bao(self, canh_bao, bo_gom):
        bo_gom.cap_nhat(canh_bao)
        for observer in self.observers:
            observer.cap_nhat(canh_bao)

    def canh_bao_ton_thap(self, ngay: date) -> list[CanhBaoDTO]:
        theo_san_pham = Counter()
        for dong in self.tra_cuu_lo_hang(BoLocLoDTO(), ngay):
            theo_san_pham[dong.ma_sp] += dong.kha_dung
        bo_gom = CanhBaoTonThapObserver()
        for sp in self.san_pham_repo.tim_tat_ca():
            kha_dung = theo_san_pham[sp.ma_sp]
            if sp.co_the_ban() and kha_dung < self.cau_hinh.nguong_ton_kho:
                self._phat_canh_bao(CanhBaoDTO(
                    LoaiCanhBao.TON_THAP, f"{sp.ten_sp} còn {kha_dung} {sp.don_vi_tinh} khả dụng.",
                    ma_sp=sp.ma_sp, so_kha_dung=kha_dung,
                ), bo_gom)
        return bo_gom.danh_sach

    def canh_bao_sap_het_han(self, ngay: date) -> list[CanhBaoDTO]:
        bo_gom = CanhBaoSapHetHanObserver()
        for lo in self.lo_hang_repo.tim_con_ton():
            so_ngay = lo.so_ngay_den_han(ngay)
            if so_ngay is not None and 0 <= so_ngay <= self.cau_hinh.so_ngay_canh_bao:
                self._phat_canh_bao(CanhBaoDTO(
                    LoaiCanhBao.SAP_HET_HAN, f"Lô {lo.ma_lo} còn {so_ngay} ngày đến hạn.",
                    ma_sp=lo.san_pham.ma_sp, ma_lo=lo.ma_lo, han_su_dung=lo.han_su_dung,
                ), bo_gom)
        return bo_gom.danh_sach

    def xem_canh_bao(self) -> KetQuaCanhBaoDTO:
        ngay = date.today()
        return KetQuaCanhBaoDTO(self.canh_bao_ton_thap(ngay), self.canh_bao_sap_het_han(ngay))
