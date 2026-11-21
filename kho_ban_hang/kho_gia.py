from kho_ban_hang.contracts.kho_contract import ChiTietDatHangDTO, IKho
from kho_ban_hang.contracts.san_pham_contract import ITraCuuSanPham
from kho_ban_hang.domain.danh_muc import DanhMuc
from kho_ban_hang.domain.enums_kho import TrangThaiDanhMuc, TrangThaiSanPham
from kho_ban_hang.domain.errors import KhongTimThayError
from kho_ban_hang.domain.errors_kho import KhongDuTonKhoError
from kho_ban_hang.domain.san_pham import HangThoiTrang, SanPham

_DANH_MUC_GIA = DanhMuc("DMGIA", "Danh mục giả", "", TrangThaiDanhMuc.HOAT_DONG)


def tao_san_pham_gia(ma_sp: str, ten_sp: str, gia_niem_yet: int, kinh_doanh: bool = True) -> SanPham:
    trang_thai = TrangThaiSanPham.KINH_DOANH if kinh_doanh else TrangThaiSanPham.NGUNG_KINH_DOANH
    return HangThoiTrang(ma_sp, ten_sp, gia_niem_yet, "cái", trang_thai, _DANH_MUC_GIA, "M", "Cotton")


class SanPhamGia(ITraCuuSanPham):
    def __init__(self, san_pham: list[SanPham] | None = None):
        self.ds = {s.ma_sp: s for s in (san_pham or [])}

    def tim_tat_ca(self):
        return list(self.ds.values())

    def tim_theo_ma(self, ma_sp):
        if ma_sp not in self.ds:
            raise KhongTimThayError(f"Không tìm thấy sản phẩm {ma_sp}.", "ma_sp")
        return self.ds[ma_sp]


class KhoGia(IKho):
    def __init__(self, ton: dict[str, int]):
        self.ton, self.giu, self.nhat_ky = dict(ton), {}, []

    def con_lai(self, ma_sp: str) -> int:
        da_giu = sum(sl for dong in self.giu.values() for m, sl in dong if m == ma_sp)
        return self.ton.get(ma_sp, 0) - da_giu

    def lay_so_luong_kha_dung(self, ma_sp: str) -> int:
        return self.con_lai(ma_sp)

    def giu_hang(self, ma_don, dong: list[ChiTietDatHangDTO]):
        for d in dong:                               # kiểm tra hết rồi mới giữ: tất cả hoặc không gì
            if self.con_lai(d.ma_sp) < d.so_luong:
                raise KhongDuTonKhoError(f"Sản phẩm {d.ma_sp} không đủ tồn để giữ hàng")
        self.giu[ma_don] = [(d.ma_sp, d.so_luong) for d in dong]

    def xac_nhan_xuat_kho(self, ma_don):
        for ma_sp, sl in self.giu.pop(ma_don, []):
            self.ton[ma_sp] -= sl
        self.nhat_ky.append(("XUAT", ma_don))

    def hoan_giu_hang(self, ma_don):
        self.giu.pop(ma_don, None)
        self.nhat_ky.append(("HOAN", ma_don))
