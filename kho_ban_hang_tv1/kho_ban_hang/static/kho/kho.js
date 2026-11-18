import { goiApi } from "../chung/api.js";

const api = "/api/kho";
const phieuPath = "/kho/phieu-nhap/";
const number = new Intl.NumberFormat("vi-VN");
const dateText = (value) => value ? value.split("-").reverse().join("/") : "—";

function hienLoi(loi, form) {
  const notice = document.querySelector("[data-error]");
  if (!notice) return;
  notice.hidden = !loi;
  notice.textContent = loi?.message || "";
  if (!loi) return;
  if (form && loi.truong) {
    const match = /^dong\[(\d+)\]\.(\w+)$/.exec(loi.truong);
    const field = match
      ? form.querySelectorAll("fieldset")[Number(match[1])]?.elements.namedItem(match[2])
      : form.elements.namedItem(loi.truong);
    if (field?.focus) {
      field.setAttribute("aria-invalid", "true");
      field.focus();
      return;
    }
  }
  notice.scrollIntoView({ block: "nearest" });
}

function dienBang(tbody, rows) {
  tbody.replaceChildren();
  for (const values of rows) {
    const row = tbody.insertRow();
    for (const value of values) row.insertCell().textContent = value ?? "—";
  }
}

async function dashboard(section) {
  const [lo, canhBao] = await Promise.all([goiApi(api + "/lo-hang"), goiApi(api + "/canh-bao")]);
  section.querySelector("[data-lots]").textContent = number.format(lo.length);
  section.querySelector("[data-low]").textContent = number.format(canhBao.ton_thap.length);
  section.querySelector("[data-expiring]").textContent = number.format(canhBao.sap_het_han.length);
}

function formPhieu(form) {
  const rows = form.querySelector("[data-rows]");
  const template = form.querySelector("[data-row-template]");
  const save = form.querySelector('button[type="submit"]');

  function danhSo() {
    rows.querySelectorAll("fieldset").forEach((row, index) => {
      row.querySelector("[data-row-title]").textContent = "Dòng " + (index + 1);
      row.querySelector("[data-remove-row]").disabled = rows.children.length === 1;
    });
  }

  function themDong(focus = false) {
    const newRow = template.content.firstElementChild.cloneNode(true);
    const sp = newRow.elements.namedItem("ma_sp");
    sp.addEventListener("change", () => {
      const canNgay = sp.selectedOptions[0]?.dataset.food === "yes";
      newRow.elements.namedItem("ngay_san_xuat").required = canNgay;
      newRow.elements.namedItem("han_su_dung").required = canNgay;
    });
    newRow.querySelector("[data-remove-row]").addEventListener("click", () => {
      newRow.remove();
      danhSo();
      form.querySelector("[data-add-row]").focus();
    });
    rows.append(newRow);
    danhSo();
    if (focus) sp.focus();
  }

  themDong();
  form.querySelector("[data-add-row]").addEventListener("click", () => themDong(true));
  form.addEventListener("input", ({ target }) => target.removeAttribute("aria-invalid"));
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    hienLoi(null);
    form.querySelectorAll('[aria-invalid="true"]').forEach((el) => el.removeAttribute("aria-invalid"));
    const dong = Array.from(rows.children, ({ elements }) => {
      const get = (name) => elements.namedItem(name).value;
      return {
        ma_sp: get("ma_sp"), ma_lo: get("ma_lo").trim(),
        so_luong_nhap: Number(get("so_luong_nhap")), gia_nhap: Number(get("gia_nhap")),
        ngay_san_xuat: get("ngay_san_xuat") || null, han_su_dung: get("han_su_dung") || null,
      };
    });
    save.disabled = true;
    try {
      const phieu = await goiApi(api + "/phieu-nhap", {
        method: "POST",
        body: { ma_ncc: form.elements.ma_ncc.value, ngay_nhap: form.elements.ngay_nhap.value, dong },
      });
      location.assign(phieuPath + encodeURIComponent(phieu.ma_phieu));
    } catch (error) {
      hienLoi(error, form);
    } finally {
      save.disabled = false;
    }
  });
}

async function chiTietPhieu(section) {
  const path = api + "/phieu-nhap/" + encodeURIComponent(section.dataset.receipt);
  const nutXacNhan = section.querySelector("[data-confirm]");
  const feedback = section.querySelector("[data-feedback]");
  const loading = section.querySelector("[data-loading]");
  function hienPhieu(phieu) {
    const daXacNhan = phieu.trang_thai === "DA_XAC_NHAN";
    const badge = section.querySelector("[data-status]");
    badge.textContent = daXacNhan ? "Đã xác nhận" : "Nháp";
    badge.classList.toggle("success", daXacNhan);
    section.querySelector("[data-supplier]").textContent = phieu.ma_ncc;
    section.querySelector("[data-date]").textContent = dateText(phieu.ngay_nhap);
    section.querySelector("[data-employee]").textContent = phieu.ma_nv;
    dienBang(section.querySelector("tbody"), phieu.dong.map((dong) => [
      dong.ma_sp, dong.ma_lo, number.format(dong.so_luong_nhap), number.format(dong.gia_nhap),
      dateText(dong.ngay_san_xuat), dateText(dong.han_su_dung),
    ]));
    nutXacNhan.hidden = daXacNhan;
    section.querySelector("[data-details]").hidden = false;
  }
  try {
    hienPhieu(await goiApi(path));
  } finally {
    loading.hidden = true;
  }
  nutXacNhan.addEventListener("click", async () => {
    hienLoi(null);
    nutXacNhan.disabled = true;
    try {
      hienPhieu(await goiApi(path + "/xac-nhan", { method: "POST", body: {} }));
      feedback.textContent = "Đã xác nhận phiếu và cập nhật tồn kho.";
      feedback.hidden = false;
    } catch (error) {
      hienLoi(error);
    } finally {
      nutXacNhan.disabled = false;
    }
  });
}

function danhSachLo(section) {
  const form = section.querySelector("form");
  const summary = section.querySelector("[data-lot-summary]");
  const tbody = section.querySelector("tbody");
  let request;
  const params = new URLSearchParams(location.search);
  for (const key of ["ma_lo", "ma_sp"]) form.elements[key].value = params.get(key) || "";
  async function load() {
    request?.abort();
    request = new AbortController();
    const query = new URLSearchParams();
    for (const key of ["ma_lo", "ma_sp"]) {
      const value = form.elements[key].value.trim();
      if (value) query.set(key, value);
    }
    const suffix = query.size ? "?" + query : "";
    history.replaceState(null, "", location.pathname + suffix);
    hienLoi(null);
    summary.textContent = "Đang tải lô hàng…";
    tbody.replaceChildren();
    try {
      const rows = await goiApi(api + "/lo-hang" + suffix, { signal: request.signal });
      summary.textContent = rows.length ? number.format(rows.length) + " lô hàng" : "Không tìm thấy lô phù hợp.";
      dienBang(tbody, rows.map((row) => [
        row.ma_lo, row.ma_sp, dateText(row.ngay_nhap), dateText(row.ngay_san_xuat), dateText(row.han_su_dung),
        number.format(row.ton_thuc_te), number.format(row.dang_giu), number.format(row.kha_dung),
      ]));
    } catch (error) {
      if (error.name !== "AbortError") {
        summary.textContent = "";
        hienLoi(error);
      }
    }
  }
  form.addEventListener("submit", (event) => { event.preventDefault(); load(); });
  form.addEventListener("reset", () => setTimeout(load, 0));
  load();
}

async function danhSachCanhBao(section) {
  const groups = [
    ["[data-low-list]", "ton_thap", "Không có sản phẩm dưới ngưỡng."],
    ["[data-expiring-list]", "sap_het_han", "Không có lô sắp hết hạn."],
  ];
  let result;
  try {
    result = await goiApi(api + "/canh-bao");
  } catch (error) {
    for (const [selector] of groups) section.querySelector(selector).replaceChildren();
    throw error;
  }
  for (const [selector, key, empty] of groups) {
    const list = section.querySelector(selector);
    list.replaceChildren();
    if (!result[key].length) {
      const item = list.appendChild(document.createElement("li"));
      item.textContent = empty;
      item.className = "muted";
      continue;
    }
    for (const warning of result[key]) {
      const item = list.appendChild(document.createElement("li"));
      const link = item.appendChild(document.createElement("a"));
      const filter = warning.ma_lo ? { ma_lo: warning.ma_lo } : { ma_sp: warning.ma_sp };
      link.href = "/kho/lo-hang?" + new URLSearchParams(filter);
      link.textContent = warning.ma_lo || warning.ma_sp;
      const text = item.appendChild(document.createElement("span"));
      text.textContent = warning.noi_dung + (warning.han_su_dung ? " · " + dateText(warning.han_su_dung) : "");
    }
  }
}

document.querySelector("[data-find-receipt]")?.addEventListener("submit", (event) => {
  event.preventDefault();
  const maPhieu = event.currentTarget.elements.ma_phieu.value.trim();
  if (maPhieu) location.assign(phieuPath + encodeURIComponent(maPhieu));
});

for (const [selector, init] of [
  ["[data-dashboard]", dashboard], ["[data-receipt-form]", formPhieu], ["[data-receipt]", chiTietPhieu],
  ["[data-lot-list]", danhSachLo], ["[data-alert-list]", danhSachCanhBao],
]) {
  const section = document.querySelector(selector);
  if (section) Promise.resolve().then(() => init(section)).catch(hienLoi);
}
