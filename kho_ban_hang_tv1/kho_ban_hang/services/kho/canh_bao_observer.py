from ...contracts.kho_contract import CanhBaoDTO, IKhoObserver
from ...domain.enums_kho import LoaiCanhBao


class CanhBaoTonThapObserver(IKhoObserver):
    def __init__(self):
        self.danh_sach: list[CanhBaoDTO] = []

    def cap_nhat(self, canh_bao: CanhBaoDTO) -> None:
        if canh_bao.loai == LoaiCanhBao.TON_THAP:
            self.danh_sach.append(canh_bao)


class CanhBaoSapHetHanObserver(IKhoObserver):
    def __init__(self):
        self.danh_sach: list[CanhBaoDTO] = []

    def cap_nhat(self, canh_bao: CanhBaoDTO) -> None:
        if canh_bao.loai == LoaiCanhBao.SAP_HET_HAN:
            self.danh_sach.append(canh_bao)
