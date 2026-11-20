from dataclasses import asdict, is_dataclass
from datetime import date, datetime

from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from ..contracts.kho_dto import BoLocLoDTO, DongNhapDTO, PhieuNhapDTO
from ..repositories.kho.kho_truy_van_repository import khop_tu_khoa
from ..domain.errors import ChuaDangNhapError, DuLieuKhongHopLeError


def _chuoi(gia_tri, truong):
    if not isinstance(gia_tri, str) or not gia_tri.strip() or len(gia_tri.strip()) > 64:
        raise DuLieuKhongHopLeError("Nhập mã từ 1 đến 64 ký tự.", truong)
    return gia_tri.strip()


def _so_nguyen(gia_tri, truong):
    if type(gia_tri) is not int or not 1 <= gia_tri <= 2**53 - 1:
        raise DuLieuKhongHopLeError("Nhập số nguyên dương trong phạm vi hỗ trợ.", truong)
    return gia_tri


def _ngay(gia_tri, truong, tuy_chon=False):
    if gia_tri is None and tuy_chon:
        return None
    try:
        ket_qua = date.fromisoformat(gia_tri)
        if ket_qua.isoformat() == gia_tri:
            return ket_qua
    except (TypeError, ValueError):
        pass
    raise DuLieuKhongHopLeError("Ngày phải có định dạng YYYY-MM-DD.", truong)


def _doc_phieu(du_lieu) -> PhieuNhapDTO:
    if not isinstance(du_lieu, dict):
        raise DuLieuKhongHopLeError("Gửi nội dung JSON của phiếu nhập.")
    ma_ncc = _chuoi(du_lieu.get("ma_ncc"), "ma_ncc")
    ngay_nhap = _ngay(du_lieu.get("ngay_nhap"), "ngay_nhap")
    cac_dong = du_lieu.get("dong")
    if not isinstance(cac_dong, list) or not cac_dong:
        raise DuLieuKhongHopLeError("Phiếu cần ít nhất một dòng hàng.", "dong")
    ket_qua = []
    for i, dong in enumerate(cac_dong):
        tien_to = f"dong[{i}]."
        if not isinstance(dong, dict):
            raise DuLieuKhongHopLeError("Dòng hàng phải là một đối tượng JSON.", f"dong[{i}]")
        ket_qua.append(DongNhapDTO(
            _chuoi(dong.get("ma_sp"), tien_to + "ma_sp"),
            _chuoi(dong.get("ma_lo"), tien_to + "ma_lo"),
            _so_nguyen(dong.get("so_luong_nhap"), tien_to + "so_luong_nhap"),
            _so_nguyen(dong.get("gia_nhap"), tien_to + "gia_nhap"),
            _ngay(dong.get("ngay_san_xuat"), tien_to + "ngay_san_xuat", tuy_chon=True),
            _ngay(dong.get("han_su_dung"), tien_to + "han_su_dung", tuy_chon=True),
        ))
    return PhieuNhapDTO(ma_ncc, ngay_nhap, ket_qua)


def _json_hoa(gia_tri):
    if is_dataclass(gia_tri):
        return _json_hoa(asdict(gia_tri))
    if isinstance(gia_tri, (date, datetime)):
        return gia_tri.isoformat()
    if isinstance(gia_tri, list):
        return [_json_hoa(item) for item in gia_tri]
    if isinstance(gia_tri, dict):
        return {key: _json_hoa(value) for key, value in gia_tri.items()}
    return gia_tri


def tao_kho_blueprint(lay_controller, lay_ma_phien, kiem_tra_csrf, endpoint_dang_nhap):
    bp = Blueprint("kho", __name__)

    def trang(ten, chuan_bi=None, **bien):
        controller = lay_controller()
        try:
            nhan_vien = controller.yeu_cau_nhan_vien_kho(lay_ma_phien())
        except ChuaDangNhapError:
            return redirect(url_for(endpoint_dang_nhap))
        if chuan_bi is not None:
            bien.update(chuan_bi(controller))
        return render_template(f"kho/{ten}.html", nhan_vien=nhan_vien, **bien)

    @bp.get("/kho")
    def index():
        return trang("index", lambda c: {
            "phieu_list": c.danh_sach_phieu(lay_ma_phien())[:5],
            "ngay_hom_nay": date.today().strftime("%d/%m/%Y"),
            "danh_muc": c.du_lieu_giao_dien(lay_ma_phien()),
        })

    @bp.get("/kho/phieu-nhap/moi")
    def phieu_nhap_moi():
        return trang("phieu_nhap_moi", lambda c: {
            "ngay_hom_nay": date.today().isoformat(),
            "san_pham": c.thanh_phan_kho.san_pham_repo.tim_tat_ca(),
            "nha_cung_cap": [ncc for ncc in c.thanh_phan_kho.nha_cung_cap_repo.tim_tat_ca() if ncc.dang_hoat_dong()],
        })

    @bp.get("/kho/phieu-nhap")
    def danh_sach_phieu():
        q = request.args.get("q", "").strip()[:120]
        status = request.args.get("trang_thai", "")
        if status not in ("", "NHAP", "DA_XAC_NHAN"):
            status = ""
        return trang("danh_sach_phieu", lambda c: {
            "phieu_list": c.danh_sach_phieu(lay_ma_phien(), q, status), "q": q, "status": status,
        })

    @bp.get("/kho/san-pham")
    def san_pham():
        return trang("san_pham", lambda c: c.du_lieu_giao_dien(lay_ma_phien()))

    @bp.get("/kho/phieu-nhap/<ma_phieu>")
    def phieu_nhap_chi_tiet(ma_phieu):
        return trang("phieu_nhap_chi_tiet", lambda c: {"danh_muc": c.du_lieu_giao_dien(lay_ma_phien())}, ma_phieu=ma_phieu)

    @bp.get("/kho/lo-hang")
    def lo_hang():
        return trang("lo_hang", lambda c: {"danh_muc": c.du_lieu_giao_dien(lay_ma_phien())})

    @bp.get("/kho/canh-bao")
    def canh_bao():
        return trang("canh_bao", lambda c: {"danh_muc": c.du_lieu_giao_dien(lay_ma_phien())})

    @bp.before_request
    def bao_ve_api_kho():
        if request.path.startswith("/api/kho/"):
            lay_controller().yeu_cau_nhan_vien_kho(lay_ma_phien())
            if request.method == "POST":
                kiem_tra_csrf(request.headers.get("X-CSRF-Token"))

    @bp.post("/api/kho/phieu-nhap")
    def api_lap_phieu():
        phieu = lay_controller().lap_phieu_nhap(lay_ma_phien(), _doc_phieu(request.get_json(silent=True)))
        return jsonify(du_lieu=_json_hoa(phieu)), 201

    @bp.get("/api/kho/phieu-nhap/<ma_phieu>")
    def api_tra_phieu(ma_phieu):
        return jsonify(du_lieu=_json_hoa(lay_controller().tra_cuu_phieu_nhap(lay_ma_phien(), ma_phieu)))

    @bp.post("/api/kho/phieu-nhap/<ma_phieu>/xac-nhan")
    def api_xac_nhan(ma_phieu):
        return jsonify(du_lieu=_json_hoa(lay_controller().xac_nhan_phieu_nhap(lay_ma_phien(), ma_phieu)))

    @bp.get("/api/kho/lo-hang")
    def api_lo_hang():
        loc = BoLocLoDTO(request.args.get("ma_lo", "").strip() or None, request.args.get("ma_sp", "").strip() or None)
        return jsonify(du_lieu=_json_hoa(lay_controller().theo_doi_lo_hang(lay_ma_phien(), loc)))

    @bp.get("/api/kho/canh-bao")
    def api_canh_bao():
        return jsonify(du_lieu=_json_hoa(lay_controller().xem_canh_bao_ton_kho(lay_ma_phien())))

    return bp
