from flask import Blueprint, render_template, request
from kho_ban_hang.repositories.phan_trang import doc_phan_trang

from kho_ban_hang.domain.enums_chung import VaiTro
from kho_ban_hang.web.chung import bao_ve_trang, container, doc_cookie, doc_json, tra_phan_hoi

bp = Blueprint("ban_hang", __name__)
API = "/api/ban-hang"


def _trang(mau, **ngu_canh):
    chan = bao_ve_trang(VaiTro.NV_BAN_HANG)
    return chan or render_template(mau, **ngu_canh)


# ---- trang HTML ----
@bp.get("/ban-hang")
def trang_chu(): return _trang("ban_hang/index.html", tab="don_hang")


@bp.get("/ban-hang/don-hang/moi")
def trang_don_moi(): return _trang("ban_hang/don_hang_moi.html")


@bp.get("/ban-hang/don-hang")
def trang_danh_sach_don(): return _trang("ban_hang/index.html", tab="don_hang")


@bp.get("/ban-hang/don-hang/<ma_don>")
def trang_don(ma_don): return _trang("ban_hang/don_hang_chi_tiet.html", ma_don=ma_don)


@bp.get("/ban-hang/don-hang/<ma_don>/hoa-don")
def trang_hoa_don(ma_don): return _trang("ban_hang/hoa_don.html", ma_don=ma_don)


@bp.get("/ban-hang/khach-hang")
def trang_khach_hang(): return _trang("ban_hang/index.html", tab="khach_hang")


@bp.get("/ban-hang/thong-ke")
def trang_thong_ke(): return _trang("ban_hang/index.html", tab="thong_ke")


@bp.get("/ban-hang/tra-cuu-kho")
def trang_tra_cuu_kho(): return _trang("ban_hang/index.html", tab="tra_cuu_kho")


# ---- API ----
@bp.post(f"{API}/don-hang")
def lap_don():
    return tra_phan_hoi(container().ban_hang_controller.lap_don_va_giu_hang(doc_cookie(), doc_json()))


@bp.get(f"{API}/don-hang")
def lay_danh_sach_don():
    tt = request.args.get("trang_thai") or None
    tk = request.args.get("tu_khoa") or None
    return tra_phan_hoi(container().ban_hang_controller.lay_danh_sach_don_hang(doc_cookie(), tt, tk, *doc_phan_trang(request.args)))


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


@bp.get(f"{API}/san-pham-goi-y")
def san_pham_goi_y():
    return tra_phan_hoi(container().ban_hang_controller.lay_san_pham_goi_y(doc_cookie()))


@bp.get(f"{API}/tra-cuu-kho")
def tra_cuu_kho():
    tk = request.args.get("tu_khoa") or None
    return tra_phan_hoi(container().ban_hang_controller.tra_cuu_kho(doc_cookie(), tk))


@bp.get(f"{API}/ma-khoi-tao")
def ma_khoi_tao():
    return tra_phan_hoi(container().ban_hang_controller.lay_ma_khoi_tao(doc_cookie()))


@bp.get(f"{API}/khach-hang")
def lay_khach_hang():
    tk = request.args.get("tu_khoa")
    if tk is not None:
        return tra_phan_hoi(container().ban_hang_controller.tra_cuu_khach_hang(doc_cookie(), tk, *doc_phan_trang(request.args)))
    return tra_phan_hoi(container().ban_hang_controller.lay_danh_sach_khach_hang(doc_cookie(), *doc_phan_trang(request.args)))


@bp.post(f"{API}/khach-hang")
def them_khach_hang():
    return tra_phan_hoi(container().ban_hang_controller.them_khach_hang(doc_cookie(), doc_json()))


@bp.get(f"{API}/khach-hang/<ma_kh>/don-hang")
def lich_su_khach_hang(ma_kh):
    return tra_phan_hoi(container().ban_hang_controller.lay_lich_su_khach_hang(doc_cookie(), ma_kh))


@bp.get(f"{API}/thong-ke/doanh-thu")
def thong_ke_doanh_thu():
    kieu = request.args.get("kieu") or "ngay"
    return tra_phan_hoi(container().ban_hang_controller.thong_ke_doanh_thu(doc_cookie(), kieu))


@bp.get(f"{API}/thong-ke/san-pham")
def thong_ke_san_pham():
    return tra_phan_hoi(container().ban_hang_controller.thong_ke_san_pham(doc_cookie()))
