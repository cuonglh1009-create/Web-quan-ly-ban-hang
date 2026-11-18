const Api = {
  csrf: null,
  phien: null,

  async goi(phuongThuc, url, thanBody) {
    const tieuDe = { Accept: "application/json" };
    if (phuongThuc !== "GET") {
      tieuDe["Content-Type"] = "application/json";
      tieuDe["X-CSRF-Token"] = Api.csrf;          // gửi cho mọi POST
    }
    const r = await fetch(url, { method: phuongThuc, headers: tieuDe, credentials: "same-origin",
      body: phuongThuc === "GET" ? undefined : JSON.stringify(thanBody ?? {}) });
    let d = null;
    try { d = await r.json(); } catch (_) { /* thân rỗng */ }
    if (!r.ok) {
      const loi = (d && d.loi) || { ma_loi: "LOI_MANG", thong_bao: "Không kết nối được máy chủ", truong: null };
      loi.status = r.status;
      throw loi;
    }
    return d.du_lieu;
  },
  get(url) { return Api.goi("GET", url); },
  post(url, body) {
    return Api.goi("POST", url, body).then((kq) => {
      if (kq && kq.csrf_token) Api.csrf = kq.csrf_token;   // đăng nhập đổi CSRF theo phiên mới
      return kq;
    });
  },

  // Lấy phiên + CSRF, dựng menu theo vai trò. batBuoc: vai trò cần có, sai thì về trang chủ.
  async khoiTao({ batBuoc } = {}) {
    const p = await Api.get("/api/xac-thuc/phien");
    Api.csrf = p.csrf_token; Api.phien = p;
    Api.dungMenu(p);
    if (batBuoc && (!p.da_dang_nhap || p.nguoi_dung.vai_tro !== batBuoc)) { location.href = "/"; }
    return p;
  },

  dungMenu(p) {
    const menu = document.getElementById("menu"), ten = document.getElementById("nguoi-dung"),
          nut = document.getElementById("nut-dang-xuat");
    if (menu) menu.replaceChildren();
    if (!p.da_dang_nhap) { ten.textContent = ""; nut.hidden = true; return; }
    if (menu) {
      const muc = p.nguoi_dung.vai_tro === "NV_KHO" ? [["/kho", "Kho"]] : [["/ban-hang", "Bán hàng"],
                    ["/ban-hang/don-hang/moi", "Lập đơn"]];
      for (const [href, nhan] of muc) {
        const a = document.createElement("a"); a.href = href; a.textContent = nhan;
        if (location.pathname === href) {
          a.setAttribute("aria-current", "page");
        }
        menu.append(a);
      }
    }
    ten.textContent = p.nguoi_dung.ho_ten;
    nut.hidden = false;
    nut.onclick = async () => { const kq = await Api.post("/api/xac-thuc/dang-xuat", {}); location.href = kq.trang_chu; };
  },

  tien(n) { return new Intl.NumberFormat("vi-VN").format(n) + " đ"; },
};
