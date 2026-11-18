"""Điểm vào Flask. Chạy: KBH_KHOA_BI_MAT=... flask --app kho_ban_hang.app run -p 5000"""
import logging
import sqlite3
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import click
from flask import Flask, jsonify, request
from werkzeug.security import generate_password_hash

from kho_ban_hang.config.cau_hinh import CauHinh
from kho_ban_hang.container import mo_ket_noi
from kho_ban_hang.domain.enums_chung import VaiTro
from kho_ban_hang.domain.errors import NghiepVuError
from kho_ban_hang.domain.errors_ban_hang import SaiCSRF, XungDot
from kho_ban_hang.domain.khach_hang import KhachThuong, KhachVIP
from kho_ban_hang.domain.khuyen_mai import KhuyenMaiPhanTram, KhuyenMaiTienMat
from kho_ban_hang.domain.nhan_vien import NhanVien
from kho_ban_hang.kho_gia import KhoGia, SanPhamGia, tao_san_pham_gia
from kho_ban_hang.services.ban_hang.xac_thuc_service import BoDemThuDangNhap
from kho_ban_hang.web import ban_hang_routes, xac_thuc_routes
from kho_ban_hang.web.kho_routes import tao_kho_blueprint
from kho_ban_hang.web.chung import container, doc_cookie, tra_loi

GOC = Path(__file__).parent
SAN_PHAM_DEMO = [tao_san_pham_gia("SP001", "Bút bi", 5_000), tao_san_pham_gia("SP002", "Vở 96 trang", 12_000),
                 tao_san_pham_gia("SP003", "Balo", 350_000)]
TON_DEMO = {"SP001": 100, "SP002": 50, "SP003": 5}
PHUONG_THUC_GHI = {"POST", "PUT", "PATCH", "DELETE"}


def tao_schema(db: sqlite3.Connection) -> None:
    db.executescript((GOC / "repositories" / "kho" / "schema_kho.sql").read_text(encoding="utf-8"))
    db.executescript((GOC / "schema_ban_hang.sql").read_text(encoding="utf-8"))


def create_app(cau_hinh: CauHinh | None = None, kho_gia=None, tra_cuu_gia=None, dong_ho=None) -> Flask:
    cau_hinh = cau_hinh or CauHinh.tu_moi_truong()
    app = Flask(__name__, template_folder="templates", static_folder="static")
    if cau_hinh.dung_kho_gia and kho_gia is None:
        kho_gia, tra_cuu_gia = KhoGia(TON_DEMO), SanPhamGia(SAN_PHAM_DEMO)
    app.extensions["kbh"] = {
        "cau_hinh": cau_hinh,
        "bo_dem_thu": BoDemThuDangNhap(cau_hinh.so_lan_thu_toi_da, cau_hinh.cua_so_thu_giay),
        "kho_gia": kho_gia, "tra_cuu_gia": tra_cuu_gia, "dong_ho": dong_ho}
    app.register_blueprint(xac_thuc_routes.bp)
    app.register_blueprint(ban_hang_routes.bp)
    app.register_blueprint(tao_kho_blueprint(
        lambda: container().kho_controller, doc_cookie,
        lambda token: container().xac_thuc.kiem_tra_csrf(doc_cookie(), token),
        "xac_thuc.trang_dang_nhap"))
    app.jinja_env.globals["csrf_token"] = lambda: container().xac_thuc.csrf_hien_tai(doc_cookie())

    @app.before_request
    def kiem_tra_csrf():   # mọi POST/PUT/PATCH/DELETE dưới /api
        if request.path.startswith("/api/") and request.method in PHUONG_THUC_GHI:
            container().xac_thuc.kiem_tra_csrf(doc_cookie(), request.headers.get("X-CSRF-Token"))

    @app.after_request
    def khong_luu_cache(resp):
        if request.path.startswith("/api/"):
            resp.headers["Cache-Control"] = "no-store"
        return resp

    @app.teardown_request
    def dong_ket_noi(_):
        from flask import g
        c = g.pop("container", None)
        if c:
            c.dong()

    @app.errorhandler(NghiepVuError)
    def loi_nghiep_vu(e): return tra_loi(e)

    @app.errorhandler(sqlite3.IntegrityError)
    def loi_rang_buoc(e):
        app.logger.warning("Vi phạm ràng buộc: %s", e)
        return tra_loi(XungDot("XUNG_DOT_DU_LIEU", "Dữ liệu xung đột với bản ghi hiện có"))

    @app.errorhandler(404)
    @app.errorhandler(405)
    def khong_khop(e):
        if request.path.startswith("/api/"):
            ma = "KHONG_TIM_THAY" if e.code == 404 else "SAI_PHUONG_THUC"
            return jsonify({"loi": {"ma_loi": ma, "thong_bao": e.description, "truong": None}}), e.code
        return e

    @app.errorhandler(Exception)
    def loi_he_thong(e):
        from werkzeug.exceptions import HTTPException
        if isinstance(e, HTTPException):
            return e
        app.logger.exception("Lỗi hệ thống")
        return jsonify({"loi": {"ma_loi": "LOI_HE_THONG", "thong_bao": "Lỗi hệ thống",
                                "truong": None}}), 500

    # ---- lệnh CLI ----
    @app.cli.command("tao-schema")
    def lenh_tao_schema():
        db = mo_ket_noi(cau_hinh.duong_dan_csdl)
        tao_schema(db)
        click.echo("Đã tạo schema.")

    @app.cli.command("seed")
    @click.option("--mat-khau-kho", prompt=True, hide_input=True, confirmation_prompt=True)
    @click.option("--mat-khau-ban-hang", prompt=True, hide_input=True, confirmation_prompt=True)
    def lenh_seed(mat_khau_kho, mat_khau_ban_hang):
        """Nạp hai tài khoản (mật khẩu nhập lúc seed, chỉ lưu bản băm) và dữ liệu mẫu Bán hàng."""
        db = mo_ket_noi(cau_hinh.duong_dan_csdl)
        tao_schema(db)
        from kho_ban_hang.repositories.ban_hang.khach_hang_repository import KhachHangRepository
        from kho_ban_hang.repositories.ban_hang.khuyen_mai_repository import KhuyenMaiRepository
        from kho_ban_hang.repositories.ban_hang.nhan_vien_repository import NhanVienRepository
        for mk in (mat_khau_kho, mat_khau_ban_hang):
            if len(mk) < 8:
                raise click.ClickException("Mật khẩu tối thiểu 8 ký tự.")
        nv = NhanVienRepository(db)
        nv.luu(NhanVien("NV001", "Nhân viên kho", VaiTro.NV_KHO, "nv_kho",
                        generate_password_hash(mat_khau_kho)))
        nv.luu(NhanVien("NV002", "Nhân viên bán hàng", VaiTro.NV_BAN_HANG, "nv_ban_hang",
                        generate_password_hash(mat_khau_ban_hang)))
        kh = KhachHangRepository(db)
        kh.luu(KhachThuong("KH001", "Nguyễn Văn A", "0900000001", "Hà Nội", 0))
        kh.luu(KhachThuong("KH002", "Trần Thị B", "0900000002", "Hà Nội", 480))
        kh.luu(KhachVIP("KH003", "Lê Văn C", "0900000003", "Hà Nội", 900, date.today()))
        km, hom_nay = KhuyenMaiRepository(db), date.today()
        chung = (hom_nay, hom_nay + timedelta(days=365))
        km.luu(KhuyenMaiPhanTram("GIAM10", "Giảm 10%", *chung, 100_000,
                                 phan_tram_giam=Decimal("10"), giam_toi_da=50_000))
        km.luu(KhuyenMaiTienMat("GIAM20K", "Giảm 20.000đ", *chung, 50_000, so_tien_giam=20_000))
        db.executescript((GOC / "repositories" / "kho" / "du_lieu_mau_kho.sql").read_text(encoding="utf-8"))
        click.echo("Đã seed: nv_kho, nv_ban_hang, KH001-KH003, GIAM10, GIAM20K, dữ liệu mẫu Kho (SP01-SP04).")

    return app


if __name__ == "__main__":
    create_app().run(port=5000, debug=False)
