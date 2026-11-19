document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("form-dang-nhap");
  const error = document.getElementById("loi");
  const submit = form.querySelector(".submit");
  const retry = document.getElementById("thu-lai");
  const password = form.elements.mat_khau;
  const toggle = form.querySelector(".password-toggle");
  let ready = false;
  let busy = false;

  function showError(text) {
    error.textContent = text;
    error.hidden = !text;
  }

  toggle.addEventListener("click", () => {
    const visible = password.type === "password";
    password.type = visible ? "text" : "password";
    toggle.textContent = visible ? "Ẩn" : "Hiện";
    toggle.setAttribute("aria-label", visible ? "Ẩn mật khẩu" : "Hiện mật khẩu");
    toggle.setAttribute("aria-pressed", String(visible));
  });

  async function connect() {
    ready = false;
    submit.disabled = true;
    retry.hidden = true;
    showError("");
    submit.firstElementChild.textContent = "Đang kết nối…";
    try {
      const phien = await Api.get('/api/xac-thuc/phien');
      Api.csrf = phien.csrf_token;
      Api.phien = phien;
      ready = true;
      submit.disabled = false;
      submit.firstElementChild.textContent = "Đăng nhập";
    } catch (_) {
      showError("Chưa kết nối được hệ thống. Vui lòng thử lại.");
      retry.hidden = false;
    }
  }

  retry.addEventListener("click", connect);
  form.addEventListener("submit", async event => {
    event.preventDefault();
    if (!ready || busy) return;
    busy = true;
    submit.disabled = true;
    submit.firstElementChild.textContent = "Đang đăng nhập…";
    showError("");
    try {
      const result = await Api.post("/api/xac-thuc/dang-nhap", {
        ten_dang_nhap: form.elements.ten_dang_nhap.value.trim(),
        mat_khau: password.value,
      });
      location.assign(result.trang_chu);
    } catch (e) {
      showError(e.thong_bao || "Không kết nối được máy chủ. Vui lòng thử lại.");
    } finally {
      busy = false;
      submit.disabled = false;
      submit.firstElementChild.textContent = "Đăng nhập";
    }
  });
  connect();
});
