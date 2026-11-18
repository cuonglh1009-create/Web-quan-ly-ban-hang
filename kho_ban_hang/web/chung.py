from flask import current_app, g, jsonify, redirect, request

from kho_ban_hang.container import Container
from kho_ban_hang.controllers.phan_hoi import PhanHoi
from kho_ban_hang.domain.errors import NghiepVuError
from kho_ban_hang.domain.errors_ban_hang import LoiDuLieu

TEN_COOKIE = "kbh_session"


def container() -> Container:
    if "container" not in g:
        e = current_app.extensions["kbh"]
        g.container = Container(e["cau_hinh"], e["bo_dem_thu"], e.get("kho_gia"),
                                e.get("tra_cuu_gia"), e.get("dong_ho"))
    return g.container


def doc_cookie() -> str | None:
    return request.cookies.get(TEN_COOKIE)


def doc_json() -> dict:
    d = request.get_json(silent=True)
    if not isinstance(d, dict):
        raise LoiDuLieu("DU_LIEU_KHONG_HOP_LE", "Thân yêu cầu phải là một đối tượng JSON")
    return d


def tra_phan_hoi(ph: PhanHoi):
    resp = jsonify({"du_lieu": ph.du_lieu})
    resp.status_code = ph.status
    cau_hinh = current_app.extensions["kbh"]["cau_hinh"]
    if ph.dat_cookie:
        resp.set_cookie(TEN_COOKIE, ph.dat_cookie, max_age=cau_hinh.thoi_han_phien_gio * 3600,
                        httponly=True, samesite="Lax", path="/",
                        secure=cau_hinh.cookie_secure or request.is_secure)
    if ph.xoa_cookie:
        resp.delete_cookie(TEN_COOKIE, path="/", httponly=True, samesite="Lax",
                           secure=cau_hinh.cookie_secure or request.is_secure)
    return resp


def tra_loi(e: NghiepVuError):
    resp = jsonify({"loi": {"ma_loi": e.ma_loi, "thong_bao": e.thong_bao, "truong": e.truong}})
    resp.status_code = e.status
    return resp


def bao_ve_trang(*vai_tro):
    """Trả None nếu được phép xem trang, ngược lại trả redirect."""
    try:
        container().xac_thuc.yeu_cau_vai_tro(doc_cookie(), *vai_tro)
        return None
    except NghiepVuError as e:
        return redirect("/dang-nhap" if e.status == 401 else "/")
