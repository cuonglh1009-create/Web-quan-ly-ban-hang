Api.khoiTao({ batBuoc: "NV_BAN_HANG" }).then(() => {
  const goc = document.getElementById("trang"), ma = goc.dataset.maDon, goi = encodeURIComponent(ma),
        $ = (id) => document.getElementById(id), loi = $("loi"),
        url = "/api/ban-hang/don-hang/" + goi;

  function xoaLoi() {
    loi.hidden = true;
    goc.querySelectorAll(".loi-truong").forEach((e) => (e.textContent = ""));
  }
  function hienLoi(e) {
    const o = e.truong && goc.querySelector(`[data-loi-truong="${e.truong}"]`);
    if (o) o.textContent = e.thong_bao; else { loi.textContent = e.thong_bao; loi.hidden = false; }
  }

  /* Tổng tiền luôn lấy từ API; nút chỉ hiện theo trạng thái. */
  function ve(d) {
    $("ma-don").textContent = d.ma_don;
    const tt = $("trang-thai");
    tt.textContent = { CHO_THANH_TOAN: "Chờ thanh toán", DA_THANH_TOAN: "Đã thanh toán",
      DA_HUY: "Đã hủy" }[d.trang_thai] || d.trang_thai;
    tt.className = "badge " + (d.trang_thai === "DA_THANH_TOAN" ? "success" : d.trang_thai === "DA_HUY" ? "danger" : "warning");

    if (d.ten_kh) {
      const khInfo = $("khach-hang-info");
      khInfo.hidden = false;
      $("ten-kh").textContent = d.ten_kh;
      $("ma-kh").textContent = d.ma_kh || "";
      const isVip = d.hang_kh === "VIP";
      $("badge-vip").hidden = !isVip;
    }

    $("tam-tinh").textContent = Api.tien(d.tam_tinh);
    $("giam-khach").textContent = (d.giam_hang_khach > 0 ? "- " : "") + Api.tien(d.giam_hang_khach);
    $("giam-km").textContent = (d.giam_khuyen_mai > 0 ? "- " : "") + Api.tien(d.giam_khuyen_mai);
    $("phai-tra").textContent = Api.tien(d.so_phai_tra);
    $("tong-hop").hidden = false;
    const cho = d.trang_thai === "CHO_THANH_TOAN";
    $("khu-km").hidden = $("khu-thanh-toan").hidden = $("nut-huy").hidden = !cho;
    const hd = $("lien-ket-hoa-don");
    hd.hidden = d.trang_thai !== "DA_THANH_TOAN";
    hd.href = "/ban-hang/don-hang/" + goi + "/hoa-don";
  }

  async function chay(viec) {
    xoaLoi();
    try { ve(await viec()); } catch (e) { hienLoi(e); }
  }

  chay(() => Api.get(url));

  $("form-km").addEventListener("submit", (ev) => {
    ev.preventDefault();
    chay(() => Api.post(url + "/khuyen-mai", { ma_km: ev.target.ma_km.value }));
  });

  const form = $("form-tt");
  form.phuong_thuc.addEventListener("change", () => {
    const ck = form.phuong_thuc.value === "CHUYEN_KHOAN";
    $("nhom-tien-mat").hidden = ck; $("nhom-chuyen-khoan").hidden = !ck;
  });
  const so = (v) => (v.trim() === "" ? null : Number(v));
  form.addEventListener("submit", async (ev) => {
    ev.preventDefault(); xoaLoi();
    const ck = form.phuong_thuc.value === "CHUYEN_KHOAN";
    const thong_tin = ck ? { so_tien_doi_soat: so(form.so_tien_doi_soat.value),
        ten_ngan_hang: form.ten_ngan_hang.value, ma_giao_dich_ngan_hang: form.ma_giao_dich_ngan_hang.value }
      : { tien_khach_dua: so(form.tien_khach_dua.value) };
    try {
      await Api.post(url + "/thanh-toan", { phuong_thuc: form.phuong_thuc.value, thong_tin });
      location.href = "/ban-hang/don-hang/" + goi + "/hoa-don";
    } catch (e) { hienLoi(e); }                    // giữ nguyên dữ liệu đã nhập
  });

  $("nut-huy").addEventListener("click", () => {
    if (!confirm("Hủy đơn " + ma + "? Hàng đang giữ sẽ được hoàn lại.")) return;   // xác nhận trước khi gửi
    chay(() => Api.post(url + "/huy", {}).then(() => Api.get(url)));
  });
});
