from datetime import date

from kho_ban_hang.contracts.ban_hang_dto import (DuLieuLapDonDTO, KetQuaHuyDonDTO, KetQuaLapDonDTO)
from kho_ban_hang.repositories.giao_dich import GiaoDich
from kho_ban_hang.contracts.kho_contract import ChiTietDatHangDTO
from kho_ban_hang.domain.don_hang import DonHang
from kho_ban_hang.domain.enums_chung import TrangThaiDonHang as TT
from kho_ban_hang.domain.errors import KhongTimThayError
from kho_ban_hang.domain.errors_ban_hang import KhongCoQuyen, KhongTimThay, LoiDuLieu, LoiNghiepVu, XungDot
from kho_ban_hang.domain.khach_hang import KhachThuong


def kiem_tra_quyen_tren_don(don: DonHang, nhan_vien) -> None:
    if don.nhan_vien.ma_nv != nhan_vien.ma_nv:
        raise KhongCoQuyen("KHONG_PHAI_DON_CUA_BAN", "Bạn không phải người lập đơn này")


class BanHangService:
    def __init__(self, kho, tra_cuu_san_pham, don_repo, khach_repo, km_repo, ket_noi, cau_hinh,
                 hom_nay=date.today):
        self.kho, self.tra_cuu, self.don_repo = kho, tra_cuu_san_pham, don_repo
        self.khach_repo, self.km_repo, self.db, self.cau_hinh = khach_repo, km_repo, ket_noi, cau_hinh
        self.hom_nay = hom_nay

    kiem_tra_quyen_tren_don = staticmethod(kiem_tra_quyen_tren_don)

    def _lay_don(self, ma_don, nhan_vien) -> DonHang:
        don = self.don_repo.tim_theo_ma(ma_don)
        if don is None:
            raise KhongTimThay("KHONG_TIM_THAY_DON", f"Không có đơn {ma_don}")
        kiem_tra_quyen_tren_don(don, nhan_vien)
        return don

    def tao_don_va_giu_hang(self, du_lieu: DuLieuLapDonDTO, nhan_vien) -> KetQuaLapDonDTO:
        with GiaoDich(self.db):   # lỗi ở bất kỳ bước nào: rollback cả đơn lẫn bản giữ
            khach = None
            if du_lieu.ma_kh:
                khach = self.khach_repo.tim_theo_ma(du_lieu.ma_kh)
                if khach is None and du_lieu.ten_kh:
                    khach = KhachThuong(du_lieu.ma_kh, du_lieu.ten_kh, du_lieu.sdt_kh or "", du_lieu.dia_chi_kh or "")
                    self.khach_repo.luu(khach)
                elif khach is None:
                    raise LoiDuLieu("KHACH_KHONG_TON_TAI", "Không có khách hàng này", "ma_kh")
            elif du_lieu.ten_kh:
                ma_moi = self.khach_repo.cap_ma_moi()
                khach = KhachThuong(ma_moi, du_lieu.ten_kh, du_lieu.sdt_kh or "", du_lieu.dia_chi_kh or "")
                self.khach_repo.luu(khach)
            don = DonHang(self.don_repo.cap_ma_moi(), self.hom_nay(), TT.NHAP, nhan_vien, khach)
            for i, d in enumerate(du_lieu.dong):
                try:
                    sp = self.tra_cuu.tim_theo_ma(d.ma_sp)
                except KhongTimThayError:
                    raise LoiDuLieu("SAN_PHAM_KHONG_TON_TAI", f"Không có sản phẩm {d.ma_sp}",
                                    f"dong[{i}].ma_sp")
                try:
                    don.them_chi_tiet(sp, d.so_luong)   # gộp mã trùng, chốt đơn giá
                except LoiNghiepVu as e:   # miền chỉ biết tên trường; service gắn số dòng
                    e.truong = f"dong[{i}].{e.truong or 'ma_sp'}"
                    raise
            don.chot_chiet_khau_hang(self.cau_hinh)
            don.xac_nhan_cho_thanh_toan()
            self.don_repo.luu(don)   # ghi đơn trước: giu_hang của Kho có khóa ngoại tới don_hang
            self.kho.giu_hang(don.ma_don, [ChiTietDatHangDTO(c.san_pham.ma_sp, c.so_luong)
                                           for c in don.chi_tiet])   # đã gộp mã trùng
        return KetQuaLapDonDTO.tu_don_hang(don)

    def tra_cuu_don(self, ma_don, nhan_vien) -> KetQuaLapDonDTO:
        return KetQuaLapDonDTO.tu_don_hang(self._lay_don(ma_don, nhan_vien))

    def ap_dung_khuyen_mai(self, ma_don, ma_km, nhan_vien) -> KetQuaLapDonDTO:
        if not isinstance(ma_km, str) or not ma_km.strip():
            raise LoiDuLieu("TRUONG_BAT_BUOC", "Nhập mã khuyến mại", "ma_km")
        with GiaoDich(self.db):
            don = self._lay_don(ma_don, nhan_vien)
            km = self.km_repo.tim_theo_ma(ma_km.strip())
            if km is None:
                raise LoiDuLieu("KHUYEN_MAI_KHONG_TON_TAI", "Mã khuyến mại không tồn tại", "ma_km")
            don.ap_dung_khuyen_mai(km, self.hom_nay())
            self.don_repo.luu(don)
        return KetQuaLapDonDTO.tu_don_hang(don)

    def huy_don(self, ma_don, nhan_vien) -> KetQuaHuyDonDTO:
        with GiaoDich(self.db):
            don = self._lay_don(ma_don, nhan_vien)
            if don.trang_thai == TT.DA_HUY:                 # hủy lặp: trả trạng thái cũ
                return KetQuaHuyDonDTO(don.ma_don, don.trang_thai.value)
            if don.trang_thai == TT.DA_THANH_TOAN:
                raise XungDot("DON_DA_THANH_TOAN", "Đơn đã thanh toán, không thể hủy")
            self.kho.hoan_giu_hang(don.ma_don)
            don.huy()
            self.don_repo.luu(don)
        return KetQuaHuyDonDTO(don.ma_don, don.trang_thai.value)

    def lay_san_pham_goi_y(self) -> list[dict]:
        danh_sach = []
        for sp in self.tra_cuu.tim_tat_ca():
            if not sp.co_the_ban():
                continue
            so_kha_dung = self.kho.lay_so_luong_kha_dung(sp.ma_sp)
            danh_sach.append({
                "ma_sp": sp.ma_sp,
                "ten_sp": sp.ten_sp,
                "don_vi_tinh": sp.don_vi_tinh,
                "gia_niem_yet": sp.gia_niem_yet,
                "so_kha_dung": so_kha_dung,
                "nhan_hien_thi": f"{sp.ma_sp} - {sp.ten_sp} (Giá: {sp.gia_niem_yet:,}đ | Tồn: {so_kha_dung} {sp.don_vi_tinh})"
            })
        return danh_sach

    def tra_cuu_kho(self, tu_khoa: str | None = None) -> list[dict]:
        ncc_map = {}
        try:
            sql_ncc = """
                SELECT ctpn.ma_sp, ncc.ten_ncc
                FROM chi_tiet_phieu_nhap ctpn
                JOIN phieu_nhap pn ON ctpn.ma_phieu = pn.ma_phieu
                JOIN nha_cung_cap ncc ON pn.ma_ncc = ncc.ma_ncc
                ORDER BY pn.ngay_nhap DESC
            """
            for row in self.db.execute(sql_ncc).fetchall():
                if row["ma_sp"] not in ncc_map:
                    ncc_map[row["ma_sp"]] = row["ten_ncc"]
        except Exception:
            pass

        ncc_mac_dinh = "Nhà cung cấp An Phú"
        try:
            ncc_row = self.db.execute("SELECT ten_ncc FROM nha_cung_cap WHERE trang_thai='HOAT_DONG' LIMIT 1").fetchone()
            if ncc_row:
                ncc_mac_dinh = ncc_row["ten_ncc"]
        except Exception:
            pass

        danh_sach = []
        for sp in self.tra_cuu.tim_tat_ca():
            ten_ncc = ncc_map.get(sp.ma_sp, ncc_mac_dinh)
            so_kha_dung = self.kho.lay_so_luong_kha_dung(sp.ma_sp)
            loai_sp = getattr(sp.loai, "value", str(sp.loai)) if hasattr(sp, "loai") else ""
            ten_dm = sp.danh_muc.ten_dm if hasattr(sp, "danh_muc") and sp.danh_muc else loai_sp

            if tu_khoa:
                tk = tu_khoa.lower()
                if tk not in sp.ma_sp.lower() and tk not in sp.ten_sp.lower() and tk not in ten_ncc.lower():
                    continue

            danh_sach.append({
                "ma_sp": sp.ma_sp,
                "ten_sp": sp.ten_sp,
                "danh_muc": ten_dm,
                "don_vi_tinh": sp.don_vi_tinh,
                "gia_niem_yet": sp.gia_niem_yet,
                "so_kha_dung": so_kha_dung,
                "nha_cung_cap": ten_ncc,
                "trang_thai": getattr(sp.trang_thai, "value", str(sp.trang_thai)) if hasattr(sp, "trang_thai") else "KINH_DOANH",
                "co_the_ban": sp.co_the_ban()
            })
        return danh_sach

    def lay_danh_sach_khach_hang(self) -> list[dict]:
        return self.khach_repo.tim_tat_ca()

    def tra_cuu_khach_hang(self, tu_khoa: str) -> list[dict]:
        return self.khach_repo.tra_cuu(tu_khoa)

    def them_khach_hang(self, du_lieu: dict) -> dict:
        ho_ten = (du_lieu.get("ho_ten") or "").strip()
        if not ho_ten:
            raise LoiDuLieu("TRUONG_BAT_BUOC", "Vui lòng nhập họ tên khách hàng", "ho_ten")
        ma_kh = (du_lieu.get("ma_kh") or "").strip() or self.khach_repo.cap_ma_moi()
        sdt = (du_lieu.get("so_dien_thoai") or "").strip()
        dia_chi = (du_lieu.get("dia_chi") or "").strip()

        if self.khach_repo.tim_theo_ma(ma_kh) is not None:
            raise XungDot("MA_KHACH_DA_TON_TAI", f"Mã khách hàng {ma_kh} đã tồn tại", "ma_kh")

        kh = KhachThuong(ma_kh, ho_ten, sdt, dia_chi, diem_tich_luy=0)
        self.khach_repo.luu(kh)
        return {
            "ma_kh": kh.ma_kh,
            "ho_ten": kh.ho_ten,
            "so_dien_thoai": kh.so_dien_thoai,
            "dia_chi": kh.dia_chi,
            "hang": "THUONG",
            "diem_tich_luy": 0
        }

    def lay_lich_su_khach_hang(self, ma_kh: str) -> list[dict]:
        return self.khach_repo.lay_lich_su_don_hang(ma_kh)

    def lay_ma_khoi_tao(self) -> dict:
        return {
            "ma_don_du_kien": self.don_repo.lay_ma_du_kien(),
            "ma_kh_du_kien": self.khach_repo.cap_ma_moi()
        }

    def lay_danh_sach_don_hang(self, trang_thai: str | None = None, tu_khoa: str | None = None) -> list[dict]:
        return self.don_repo.lay_danh_sach(trang_thai, tu_khoa)

    def thong_ke_doanh_thu(self, kieu: str = "ngay") -> list[dict]:
        return self.don_repo.thong_ke_doanh_thu(kieu)

    def thong_ke_san_pham(self) -> list[dict]:
        return self.don_repo.thong_ke_san_pham_ban_chay()
