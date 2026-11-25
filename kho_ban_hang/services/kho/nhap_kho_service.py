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
            # 1. Tìm hoặc tự động tạo nhà cung cấp khi người dùng gõ vào
            ncc = None
            try:
                ncc = self.nha_cung_cap_repo.tim_theo_ma(du_lieu.ma_ncc)
            except KhongTimThayError:
                pass
            if ncc is None:
                all_ncc = self.nha_cung_cap_repo.tim_tat_ca()
                ten_tim = (du_lieu.ten_ncc or du_lieu.ma_ncc).strip().lower()
                for item in all_ncc:
                    if item.ten_ncc.strip().lower() == ten_tim or item.ma_ncc.strip().lower() == ten_tim:
                        ncc = item
                        break
            if ncc is None:
                ten_ncc_moi = (du_lieu.ten_ncc or du_lieu.ma_ncc).strip()
                all_ncc = self.nha_cung_cap_repo.tim_tat_ca()
                max_ncc_num = 0
                for item in all_ncc:
                    if item.ma_ncc.startswith("NCC") and item.ma_ncc[3:].isdigit():
                        max_ncc_num = max(max_ncc_num, int(item.ma_ncc[3:]))
                from ...domain.nha_cung_cap import NhaCungCap
                from ...domain.enums_kho import TrangThaiNhaCungCap
                ncc = NhaCungCap(f"NCC{max_ncc_num + 1:02d}", ten_ncc_moi, "", "", TrangThaiNhaCungCap.HOAT_DONG)
                self.nha_cung_cap_repo.luu(ncc)

            phieu = PhieuNhapKho(
                self.phieu_nhap_repo.cap_ma_moi(), du_lieu.ngay_nhap, nguoi_lap, ncc,
            )

            # 2. Xử lý sản phẩm & mã lô tự động gán
            ma_lo_da_doc = set()
            for i, dong in enumerate(du_lieu.dong):
                ma_lo = dong.ma_lo
                if not ma_lo:
                    from uuid import uuid4
                    ma_lo = f"LO-{du_lieu.ngay_nhap.strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"
                if ma_lo in ma_lo_da_doc:
                    from uuid import uuid4
                    ma_lo = f"LO-{du_lieu.ngay_nhap.strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"
                ma_lo_da_doc.add(ma_lo)

                sp = None
                try:
                    sp = self.san_pham_repo.tim_theo_ma(dong.ma_sp)
                except KhongTimThayError:
                    pass
                if sp is None:
                    all_sp = self.san_pham_repo.tim_tat_ca()
                    ten_sp_tim = (dong.ten_sp or dong.ma_sp).strip().lower()
                    for item in all_sp:
                        if item.ten_sp.strip().lower() == ten_sp_tim or item.ma_sp.strip().lower() == ten_sp_tim:
                            sp = item
                            break
                if sp is None:
                    ten_sp_moi = (dong.ten_sp or dong.ma_sp).strip()
                    all_sp = self.san_pham_repo.tim_tat_ca()
                    max_sp_num = 0
                    for item in all_sp:
                        if item.ma_sp.startswith("SP") and item.ma_sp[2:].isdigit():
                            max_sp_num = max(max_sp_num, int(item.ma_sp[2:]))
                    ma_sp_moi = f"SP{max_sp_num + 1:02d}"

                    la_thuc_pham = dong.han_su_dung is not None or dong.ngay_san_xuat is not None
                    from ...domain.danh_muc import DanhMuc
                    from ...domain.enums_kho import LoaiSanPham, TrangThaiSanPham, TrangThaiDanhMuc
                    danh_muc_all = self.san_pham_repo.danh_muc_repo.tim_tat_ca() if hasattr(self.san_pham_repo, 'danh_muc_repo') else []
                    dm = None
                    if danh_muc_all:
                        for d in danh_muc_all:
                            if la_thuc_pham and "thực phẩm" in d.ten_dm.lower():
                                dm = d
                                break
                            elif not la_thuc_pham and "điện tử" in d.ten_dm.lower():
                                dm = d
                                break
                        if not dm:
                            dm = danh_muc_all[0]
                    else:
                        dm = DanhMuc("DM01", "Thực phẩm" if la_thuc_pham else "Điện tử", "", TrangThaiDanhMuc.HOAT_DONG)

                    loai_sp = LoaiSanPham.THUC_PHAM if la_thuc_pham else LoaiSanPham.DIEN_TU
                    from ...domain.san_pham_factory import SanPhamFactory
                    sp_dict = {
                        "ma_sp": ma_sp_moi,
                        "ten_sp": ten_sp_moi,
                        "gia_niem_yet": int(dong.gia_nhap * 1.25) if dong.gia_nhap > 0 else 100000,
                        "don_vi_tinh": "gói" if la_thuc_pham else "chiếc",
                        "trang_thai": TrangThaiSanPham.KINH_DOANH,
                        "danh_muc": dm,
                    }
                    if la_thuc_pham:
                        sp_dict["yeu_cau_bao_quan"] = "Nơi khô ráo"
                    else:
                        sp_dict["thoi_gian_bao_hanh"] = 12
                        sp_dict["cong_suat"] = "10.0"

                    sp = SanPhamFactory.tao_san_pham(loai_sp, sp_dict)
                    self.san_pham_repo.luu(sp)

                lo = LoHang(
                    ma_lo, sp, du_lieu.ngay_nhap, dong.ngay_san_xuat,
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
