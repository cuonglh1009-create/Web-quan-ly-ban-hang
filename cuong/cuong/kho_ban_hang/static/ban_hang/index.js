Api.khoiTao({ batBuoc: "NV_BAN_HANG" }).then(() => {
  const form = document.getElementById("form-tra-cuu"), loi = document.getElementById("loi");
  form.addEventListener("submit", (ev) => {
    ev.preventDefault();
    const ma = form.ma_don.value.trim();
    if (!ma) { loi.textContent = "Nhập mã đơn"; loi.hidden = false; return; }
    location.href = "/ban-hang/don-hang/" + encodeURIComponent(ma);
  });
});
