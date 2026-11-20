from dataclasses import dataclass
from datetime import date

from .enums_kho import TrangThaiPhieuNhap
from .errors import DuLieuKhongHopLeError, TrangThaiKhongHopLeError
from .lo_hang import LoHang
from .nha_cung_cap import NhaCungCap
from .nhan_vien import NhanVien
from .san_pham import SanPham


@dataclass(frozen=True)
class ChiTietPhieuNhap:
    san_pham: SanPham
    so_luong_nhap: int
    gia_nhap: int
    lo_hang: LoHang

    def kiem_tra_hop_le(self, ngay_nhap: date, tien_to: str = "") -> None:
        lo = self.lo_hang
        if lo.san_pham.ma_sp != self.san_pham.ma_sp:
            raise DuLieuKhongHopLeError("Sản phẩm của lô không khớp dòng phiếu.", tien_to + "ma_sp")
        if lo.ngay_nhap != ngay_nhap:
            raise DuLieuKhongHopLeError("Ngày nhập lô không khớp ngày phiếu.", tien_to + "ngay_nhap")
        if lo.so_luong_con_lai != self.so_luong_nhap or lo.gia_nhap != self.gia_nhap:
            raise DuLieuKhongHopLeError("Số lượng hoặc giá nhập của lô không khớp dòng phiếu.", tien_to + "so_luong_nhap")
        for ten, gia_tri in (("so_luong_nhap", self.so_luong_nhap), ("gia_nhap", self.gia_nhap)):
            if type(gia_tri) is not int or gia_tri <= 0:
                raise DuLieuKhongHopLeError("Phải là số nguyên dương.", tien_to + ten)
        if self.san_pham.can_ngay_lo:
            for ten in ("ngay_san_xuat", "han_su_dung"):
                if getattr(lo, ten) is None:
                    raise DuLieuKhongHopLeError("Thực phẩm cần khai báo ngày này.", tien_to + ten)
        if lo.ngay_san_xuat and lo.ngay_san_xuat > ngay_nhap:
            raise DuLieuKhongHopLeError("Ngày sản xuất phải trước hoặc bằng ngày nhập.", tien_to + "ngay_san_xuat")
        if lo.han_su_dung and lo.han_su_dung < ngay_nhap:
            raise DuLieuKhongHopLeError("Hạn sử dụng phải từ ngày nhập trở đi.", tien_to + "han_su_dung")


class PhieuNhapKho:
    def __init__(
        self, ma_phieu: str, ngay_nhap: date, nguoi_lap: NhanVien,
        nha_cung_cap: NhaCungCap, trang_thai=TrangThaiPhieuNhap.NHAP, chi_tiet=(),
    ):
        self.ma_phieu = ma_phieu
        self.ngay_nhap = ngay_nhap
        self.nguoi_lap = nguoi_lap
        self.nha_cung_cap = nha_cung_cap
        self._trang_thai = TrangThaiPhieuNhap(trang_thai)
        self._chi_tiet = list(chi_tiet)

    @property
    def trang_thai(self) -> TrangThaiPhieuNhap:
        return self._trang_thai

    @property
    def chi_tiet(self) -> tuple[ChiTietPhieuNhap, ...]:
        return tuple(self._chi_tiet)

    def them_chi_tiet(self, chi_tiet: ChiTietPhieuNhap) -> None:
        if self.trang_thai != TrangThaiPhieuNhap.NHAP:
            raise TrangThaiKhongHopLeError("Chỉ có thể thêm dòng vào phiếu nháp.")
        chi_tiet.kiem_tra_hop_le(self.ngay_nhap, f"dong[{len(self.chi_tiet)}].")
        self._chi_tiet.append(chi_tiet)

    def kiem_tra_truoc_xac_nhan(self, ngay_xac_nhan: date) -> None:
        if self.ngay_nhap > ngay_xac_nhan:
            raise DuLieuKhongHopLeError("Ngày nhập nằm trong tương lai.", "ngay_nhap")
        if not self.nha_cung_cap.dang_hoat_dong():
            raise DuLieuKhongHopLeError("Nhà cung cấp đã ngừng hoạt động.", "ma_ncc")
        if not self.chi_tiet:
            raise DuLieuKhongHopLeError("Phiếu phải có ít nhất một dòng.", "dong")
        for i, chi_tiet in enumerate(self.chi_tiet):
            chi_tiet.kiem_tra_hop_le(self.ngay_nhap, f"dong[{i}].")

    def xac_nhan(self, ngay_xac_nhan: date) -> list[LoHang]:
        if self.trang_thai == TrangThaiPhieuNhap.DA_XAC_NHAN:
            return []
        self.kiem_tra_truoc_xac_nhan(ngay_xac_nhan)
        self._trang_thai = TrangThaiPhieuNhap.DA_XAC_NHAN
        return [chi_tiet.lo_hang for chi_tiet in self.chi_tiet]
