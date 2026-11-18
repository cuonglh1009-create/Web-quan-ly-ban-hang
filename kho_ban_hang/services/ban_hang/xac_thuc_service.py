import hmac
import secrets
import threading
import time
from datetime import datetime, timedelta, timezone
from hashlib import sha256

from werkzeug.security import check_password_hash, generate_password_hash

from kho_ban_hang.contracts.kiem_tra_dau_vao import chuoi_bat_buoc
from kho_ban_hang.contracts.xac_thuc_contract import (IXacThuc, PhienHienTai, PhienLamViec)
from kho_ban_hang.domain.enums_chung import VaiTro
from kho_ban_hang.domain.errors_ban_hang import ChuaDangNhap, KhongCoQuyen, LoiDuLieu, QuaSoLanThu, SaiCSRF
from kho_ban_hang.domain.nhan_vien import NhanVien

_BAM_GIA = generate_password_hash("khong-ai-dung-mat-khau-nay")  # cân thời gian khi sai tên


class BoDemThuDangNhap:
    """Đếm lần đăng nhập SAI theo tên đăng nhập, trong bộ nhớ tiến trình. Chạy nhiều tiến trình thì chuyển sang bảng SQLite."""

    def __init__(self, toi_da: int, cua_so_giay: int, dong_ho=time.monotonic):
        self.toi_da, self.cua_so, self.dong_ho = toi_da, cua_so_giay, dong_ho
        self._d: dict[str, list[float]] = {}
        self._khoa = threading.Lock()

    def _don(self, k):
        moc = self.dong_ho() - self.cua_so
        self._d[k] = [t for t in self._d.get(k, []) if t > moc]
        return self._d[k]

    def bi_khoa(self, k: str) -> bool:
        with self._khoa:
            return len(self._don(k)) >= self.toi_da

    def ghi_that_bai(self, k: str) -> None:
        with self._khoa:
            self._don(k).append(self.dong_ho())

    def xoa(self, k: str) -> None:
        with self._khoa:
            self._d.pop(k, None)


class XacThucService(IXacThuc):
    def __init__(self, nhan_vien_repo, phien_repo, cau_hinh, bo_dem: BoDemThuDangNhap, dong_ho=None):
        self.nv_repo, self.phien_repo, self.cau_hinh, self.bo_dem = (
            nhan_vien_repo, phien_repo, cau_hinh, bo_dem)
        self.dong_ho = dong_ho or (lambda: datetime.now(timezone.utc))

    # nội bộ
    def _bam(self, ma_phien_web: str) -> str:   # cookie giữ mã ngẫu nhiên, DB chỉ giữ bản băm
        return hmac.new(self.cau_hinh.khoa_bi_mat.encode(), ma_phien_web.encode(), sha256).hexdigest()

    def _tao_phien(self, ma_nv: str | None = None) -> tuple[str, PhienLamViec]:
        ma_web, bay_gio = secrets.token_urlsafe(32), self.dong_ho()
        phien = PhienLamViec(self._bam(ma_web), ma_nv, bay_gio if ma_nv else None,
                             bay_gio + timedelta(hours=self.cau_hinh.thoi_han_phien_gio),
                             secrets.token_urlsafe(32))
        self.phien_repo.luu(phien)
        return ma_web, phien

    def _tim_hop_le(self, ma_phien_web: str | None) -> PhienLamViec | None:
        if not ma_phien_web:
            return None
        phien = self.phien_repo.tim_theo_ma_bam(self._bam(ma_phien_web))
        if phien and phien.het_han(self.dong_ho()):
            self.phien_repo.thu_hoi(phien.ma_bam)
            return None
        return phien

    def _nhan_vien_dang_dung(self, phien: PhienLamViec) -> NhanVien | None:
        """Đọc lại từ DB mỗi lần: đổi vai trò hoặc khóa tài khoản có hiệu lực ngay."""
        nv = self.nv_repo.tim_theo_ma(phien.ma_nv) if phien.ma_nv else None
        if phien.ma_nv and (nv is None or not nv.dang_hoat_dong):
            self.phien_repo.thu_hoi(phien.ma_bam)
            return None
        return nv

    # API
    def lay_phien(self, ma_phien_web: str | None) -> PhienHienTai:
        phien = self._tim_hop_le(ma_phien_web)
        nv = self._nhan_vien_dang_dung(phien) if phien else None
        if phien is None or (phien.ma_nv and nv is None):
            ma_moi, phien = self._tao_phien()
            return PhienHienTai(phien, None, ma_moi)
        return PhienHienTai(phien, nv)

    def csrf_hien_tai(self, ma_phien_web: str | None) -> str:
        """Mã CSRF của phiên hợp lệ (không tạo phiên mới); chuỗi rỗng nếu chưa có phiên."""
        phien = self._tim_hop_le(ma_phien_web)
        return phien.csrf_token if phien else ""

    def kiem_tra_csrf(self, ma_phien_web: str | None, csrf_header: str | None) -> None:
        phien = self._tim_hop_le(ma_phien_web)
        if phien is None or not csrf_header or not hmac.compare_digest(
                phien.csrf_token.encode(), csrf_header.encode()):
            raise SaiCSRF("CSRF_KHONG_HOP_LE", "Phiên làm việc hoặc mã CSRF không hợp lệ")

    def dang_nhap(self, ten_dang_nhap, mat_khau, ma_phien_web) -> PhienHienTai:
        ten = chuoi_bat_buoc(ten_dang_nhap, "ten_dang_nhap")
        if not isinstance(mat_khau, str) or not mat_khau or len(mat_khau) > 256:
            raise LoiDuLieu("TRUONG_BAT_BUOC", "Trường này là bắt buộc", "mat_khau")
        khoa = ten.lower()
        if self.bo_dem.bi_khoa(khoa):
            raise QuaSoLanThu("QUA_SO_LAN_THU", "Thử đăng nhập quá nhiều lần, hãy đợi rồi thử lại")
        nv = self.nv_repo.tim_theo_ten_dang_nhap(ten)
        if nv is None:
            check_password_hash(_BAM_GIA, mat_khau)   # tốn thời gian như khi có tài khoản
            dung = False
        else:
            dung = nv.kiem_tra_mat_khau(mat_khau)
        if not (dung and nv.dang_hoat_dong):   # cùng một thông báo cho mọi lý do
            self.bo_dem.ghi_that_bai(khoa)
            raise ChuaDangNhap("SAI_THONG_TIN", "Tên đăng nhập hoặc mật khẩu không đúng")
        self.bo_dem.xoa(khoa)
        cu = self._tim_hop_le(ma_phien_web)
        if cu:
            self.phien_repo.thu_hoi(cu.ma_bam)           # thay phiên ẩn danh: chống session fixation
        self.phien_repo.xoa_het_han(self.dong_ho())
        ma_moi, phien = self._tao_phien(nv.ma_nv)
        return PhienHienTai(phien, nv, ma_moi)

    def dang_xuat(self, ma_phien_web) -> None:
        if ma_phien_web:
            self.phien_repo.thu_hoi(self._bam(ma_phien_web))

    def yeu_cau_vai_tro(self, ma_phien_web, *vai_tro_cho_phep: VaiTro) -> NhanVien:
        phien = self._tim_hop_le(ma_phien_web)
        nv = self._nhan_vien_dang_dung(phien) if phien else None
        if nv is None:
            raise ChuaDangNhap("CHUA_DANG_NHAP", "Cần đăng nhập")
        if vai_tro_cho_phep and not any(nv.co_vai_tro(v) for v in vai_tro_cho_phep):
            raise KhongCoQuyen("KHONG_DU_QUYEN", "Không đủ quyền thực hiện thao tác này")
        return nv
