import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from werkzeug.security import check_password_hash

from ..contracts.xac_thuc_contract import IXacThuc
from ..domain.enums_chung import TrangThaiNhanVien, VaiTro
from ..domain.errors import ChuaDangNhapError, KhongDuQuyenError, KhongTimThayError
from ..domain.nhan_vien import NhanVien


def tim_nhan_vien_demo(conn, ma_nv: str) -> NhanVien:
    row = conn.execute("SELECT * FROM nhan_vien WHERE ma_nv = ?", (ma_nv,)).fetchone()
    if row is None:
        raise KhongTimThayError(f"Không tìm thấy nhân viên {ma_nv}.")
    return NhanVien(row["ma_nv"], row["ho_ten"], VaiTro(row["vai_tro"]), row["ten_dang_nhap"],
                    row["mat_khau_hash"], TrangThaiNhanVien(row["trang_thai"]))


def _bam(ma_phien):
    return hashlib.sha256(ma_phien.encode()).hexdigest()


class XacThucDemo(IXacThuc):
    def __init__(self, conn, thoi_han_phien_gio: int):
        self.conn = conn
        self.thoi_han_phien_gio = thoi_han_phien_gio

    def dang_nhap(self, ten_dang_nhap: str, mat_khau: str) -> str | None:
        row = self.conn.execute(
            "SELECT * FROM nhan_vien WHERE ten_dang_nhap = ?", (ten_dang_nhap,)
        ).fetchone()
        if row is None or row["trang_thai"] != TrangThaiNhanVien.HOAT_DONG:
            return None
        if not check_password_hash(row["mat_khau_hash"], mat_khau):
            return None
        ma_phien = secrets.token_urlsafe(32)
        het_han = datetime.now(timezone.utc) + timedelta(hours=self.thoi_han_phien_gio)
        self.conn.execute("INSERT INTO phien_demo VALUES (?, ?, ?)", (_bam(ma_phien), row["ma_nv"], het_han.isoformat()))
        return ma_phien

    def dang_xuat(self, ma_phien_web: str | None) -> None:
        if ma_phien_web:
            self.conn.execute("DELETE FROM phien_demo WHERE ma_bam=?", (_bam(ma_phien_web),))

    def yeu_cau_vai_tro(self, ma_phien_web: str | None, *vai_tro_cho_phep: VaiTro) -> NhanVien:
        if not ma_phien_web:
            raise ChuaDangNhapError("Vui lòng đăng nhập.")
        row = self.conn.execute(
            "SELECT * FROM phien_demo WHERE ma_bam = ?", (_bam(ma_phien_web),)
        ).fetchone()
        if row is None or datetime.fromisoformat(row["het_han_luc"]) <= datetime.now(timezone.utc):
            raise ChuaDangNhapError("Phiên không còn hiệu lực. Vui lòng đăng nhập lại.")
        nhan_vien = tim_nhan_vien_demo(self.conn, row["ma_nv"])
        if nhan_vien.trang_thai != TrangThaiNhanVien.HOAT_DONG:
            raise ChuaDangNhapError("Phiên không còn hiệu lực. Vui lòng đăng nhập lại.")
        if nhan_vien.vai_tro not in vai_tro_cho_phep:
            raise KhongDuQuyenError("Tài khoản không có quyền vào phân hệ Kho.")
        return nhan_vien
