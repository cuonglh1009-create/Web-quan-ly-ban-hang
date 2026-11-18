import os
import secrets
from contextlib import closing
from pathlib import Path

import click
from flask import Flask, g, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash

from .config.cau_hinh import CauHinh
from .controllers.kho_controller import KhoController
from .demo.xac_thuc import XacThucDemo, tim_nhan_vien_demo
from .domain.enums_chung import TrangThaiNhanVien, VaiTro
from .domain.errors import CsrfKhongHopLeError, NghiepVuError
from .repositories.giao_dich import GiaoDich, ket_noi
from .services.kho.dang_ky import dang_ky_kho
from .web.kho_routes import tao_kho_blueprint


def create_app(database_path=None, test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("KBH_SECRET_KEY") or secrets.token_hex(32),
        SESSION_COOKIE_NAME="kbh_session",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        MAX_CONTENT_LENGTH=256 * 1024,
        TRUSTED_HOSTS=["localhost", "127.0.0.1"],
    )
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    duong_dan = str(database_path or os.environ.get("KBH_DB") or Path(app.instance_path) / "kho_demo.db")
    cau_hinh = CauHinh(duong_dan)

    def lay_db():
        if "db" not in g:
            g.db = ket_noi(cau_hinh.duong_dan_csdl)
        return g.db

    @app.teardown_appcontext
    def dong_db(_loi):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    def lay_xac_thuc():
        return XacThucDemo(lay_db(), cau_hinh.thoi_han_phien_gio)

    def lay_controller():
        if "controller_kho" not in g:
            db = lay_db()
            components = dang_ky_kho(db, cau_hinh, lambda ma_nv: tim_nhan_vien_demo(db, ma_nv))
            g.controller_kho = KhoController(lay_xac_thuc(), components)
        return g.controller_kho

    def csrf_token():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_urlsafe(32)
        return session["csrf_token"]

    def kiem_tra_csrf(token):
        mong_doi = session.get("csrf_token")
        if not (token and token.isascii() and mong_doi and secrets.compare_digest(token, mong_doi)):
            raise CsrfKhongHopLeError("Yêu cầu thiếu mã bảo vệ hợp lệ. Hãy tải lại trang.")

    app.jinja_env.globals["csrf_token"] = csrf_token
    app.register_blueprint(tao_kho_blueprint(
        lay_controller, lambda: session.get("ma_phien_web"), kiem_tra_csrf, "dang_nhap",
    ))

    @app.get("/")
    def index():
        return redirect(url_for("kho.index"))

    @app.route("/dang-nhap", methods=["GET", "POST"])
    def dang_nhap():
        if request.method == "GET":
            return render_template("demo/dang_nhap.html")
        kiem_tra_csrf(request.form.get("csrf_token"))
        auth = lay_xac_thuc()
        ma_phien = auth.dang_nhap(request.form.get("ten_dang_nhap", "").strip(), request.form.get("mat_khau", ""))
        if ma_phien is None:
            return render_template("demo/dang_nhap.html", loi="Tài khoản hoặc mật khẩu không hợp lệ."), 401
        auth.dang_xuat(session.get("ma_phien_web"))
        session.clear()
        session["ma_phien_web"] = ma_phien
        return redirect(url_for("kho.index"), code=303)

    @app.post("/dang-xuat")
    def dang_xuat():
        kiem_tra_csrf(request.form.get("csrf_token"))
        lay_xac_thuc().dang_xuat(session.get("ma_phien_web"))
        session.clear()
        return redirect(url_for("dang_nhap"), code=303)

    @app.errorhandler(NghiepVuError)
    def loi_nghiep_vu(loi):
        if request.path.startswith("/api/"):
            return jsonify(loi={"ma_loi": loi.ma_loi, "thong_bao": loi.thong_bao, "truong": loi.truong}), loi.status
        return render_template("demo/loi.html", loi=loi.thong_bao), loi.status

    @app.cli.command("seed-kho")
    @click.password_option("--mat-khau", prompt="Mat khau cho demo_kho")
    def seed_kho(mat_khau):
        if len(mat_khau) < 8:
            raise click.ClickException("Mat khau phai co it nhat 8 ky tu.")
        kho = Path(__file__).parent / "repositories" / "kho"
        with closing(ket_noi(cau_hinh.duong_dan_csdl)) as db:
            db.executescript((Path(__file__).parent / "demo" / "schema_demo.sql").read_text(encoding="utf-8"))
            db.executescript((kho / "schema_kho.sql").read_text(encoding="utf-8"))
            with GiaoDich(db):
                db.execute(
                    """INSERT INTO nhan_vien VALUES (?, ?, ?, ?, ?, ?)
                       ON CONFLICT(ten_dang_nhap) DO UPDATE SET mat_khau_hash = excluded.mat_khau_hash""",
                    ("NVK01", "Nhân viên kho", VaiTro.NV_KHO, "demo_kho",
                     generate_password_hash(mat_khau), TrangThaiNhanVien.HOAT_DONG),
                )
                db.execute("DELETE FROM phien_demo WHERE ma_nv = ?", ("NVK01",))
            db.executescript((kho / "du_lieu_mau_kho.sql").read_text(encoding="utf-8"))
        click.echo("Da chuan bi du lieu Kho. Tai khoan: demo_kho.")

    return app
