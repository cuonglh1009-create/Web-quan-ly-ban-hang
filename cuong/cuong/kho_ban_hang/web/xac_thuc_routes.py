from flask import Blueprint, redirect, render_template

from kho_ban_hang.controllers.xac_thuc_controller import trang_chu_cua
from kho_ban_hang.domain.errors import NghiepVuError
from kho_ban_hang.web.chung import container, doc_cookie, doc_json, tra_phan_hoi

bp = Blueprint("xac_thuc", __name__)


@bp.get("/")
def trang_goc():
    try:
        nv = container().xac_thuc.yeu_cau_vai_tro(doc_cookie())
    except NghiepVuError:
        return redirect("/dang-nhap")
    return redirect(trang_chu_cua(nv))


@bp.get("/dang-nhap")
def trang_dang_nhap():
    try:
        nv = container().xac_thuc.yeu_cau_vai_tro(doc_cookie())
        return redirect(trang_chu_cua(nv))
    except NghiepVuError:
        return render_template("xac_thuc/dang_nhap.html")


@bp.get("/api/xac-thuc/phien")
def lay_phien():
    return tra_phan_hoi(container().xac_thuc_controller.lay_phien(doc_cookie()))


@bp.post("/api/xac-thuc/dang-nhap")
def dang_nhap():
    return tra_phan_hoi(container().xac_thuc_controller.dang_nhap(doc_cookie(), doc_json()))


@bp.post("/api/xac-thuc/dang-xuat")
def dang_xuat():
    return tra_phan_hoi(container().xac_thuc_controller.dang_xuat(doc_cookie()))
