from flask import Blueprint, render_template

from kho_ban_hang.domain.enums_chung import VaiTro
from kho_ban_hang.web.chung import bao_ve_trang, container, doc_cookie, doc_json, tra_phan_hoi

bp = Blueprint("ban_hang", __name__)
API = "/api/ban-hang"


def _trang(mau, **ngu_canh):
    chan = bao_ve_trang(VaiTro.NV_BAN_HANG)
    return chan or render_template(mau, **ngu_canh)


# ---- trang HTML ----
@bp.get("/ban-hang")
def trang_chu(): return _trang("ban_hang/index.html")


@bp.get("/ban-hang/don-hang/moi")
def trang_don_moi(): return _trang("ban_hang/don_hang_moi.html")


@bp.get("/ban-hang/don-hang/<ma_don>")
def trang_don(ma_don): return _trang("ban_hang/don_hang_chi_tiet.html", ma_don=ma_don)


@bp.get("/ban-hang/don-hang/<ma_don>/hoa-don")
def trang_hoa_don(ma_don): return _trang("ban_hang/hoa_don.html", ma_don=ma_don)


# ---- API ----
@bp.post(f"{API}/don-hang")
def lap_don():
    return tra_phan_hoi(container().ban_hang_controller.lap_don_va_giu_hang(doc_cookie(), doc_json()))


@bp.get(f"{API}/don-hang/<ma_don>")
def tra_cuu_don(ma_don):
    return tra_phan_hoi(container().ban_hang_controller.tra_cuu_don(doc_cookie(), ma_don))


@bp.post(f"{API}/don-hang/<ma_don>/khuyen-mai")
def ap_ma(ma_don):
    return tra_phan_hoi(container().ban_hang_controller.ap_dung_khuyen_mai(
        doc_cookie(), ma_don, doc_json()))


@bp.post(f"{API}/don-hang/<ma_don>/thanh-toan")
def thanh_toan(ma_don):
    return tra_phan_hoi(container().ban_hang_controller.thanh_toan_va_xuat_hoa_don(
        doc_cookie(), ma_don, doc_json()))


@bp.get(f"{API}/don-hang/<ma_don>/hoa-don")
def hoa_don(ma_don):
    return tra_phan_hoi(container().ban_hang_controller.tra_cuu_hoa_don(doc_cookie(), ma_don))


@bp.post(f"{API}/don-hang/<ma_don>/huy")
def huy(ma_don):
    doc_json()   # nhận {}
    return tra_phan_hoi(container().ban_hang_controller.huy_don(doc_cookie(), ma_don))
