import { goiApi } from "../chung/api.js";

const api = "/api/kho";
const phieuPath = "/kho/phieu-nhap/";
const number = new Intl.NumberFormat("vi-VN");
const money = value => number.format(value) + " ₫";
const dateText = value => value ? value.split("-").reverse().join("/") : "—";
const catalog = JSON.parse(document.querySelector("#du-lieu-kho")?.textContent || "{}");
const products = new Map((catalog.san_pham || []).map(p => [p.ma_sp, p]));
const suppliers = new Map((catalog.nha_cung_cap || []).map(p => [p.ma_ncc, p.ten_ncc]));
const normalize = value => (value || "").toLocaleLowerCase("vi").replaceAll("đ","d")
  .normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim();

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

function cell(row, text, className="") {
  const td = row.insertCell();
  td.textContent = text ?? "—";
  td.className = className;
  return td;
}

function badge(text, className) {
  const span = document.createElement("span");
  span.className = "badge " + className;
  span.textContent = text;
  return span;
}

function lotStatus(row) {
  const today = new Date();
  const current = Date.UTC(today.getFullYear(), today.getMonth(), today.getDate());
  const expiry = row.han_su_dung ? Date.parse(row.han_su_dung + "T00:00:00Z") : null;
  if (expiry !== null && expiry < current) return ["Đã hết hạn", "danger", "het_han"];
  if (row.ton_thuc_te === 0) return ["Hết hàng", "neutral", "het_hang"];
  if (expiry !== null && expiry <= current + catalog.so_ngay_canh_bao * 86400000) return ["Sắp hết hạn", "pending", "sap_het_han"];
  if (row.kha_dung === 0) return ["Không khả dụng", "neutral", "khong_kha_dung"];
  return ["Còn khả dụng", "success", "con_hang"];
}

function tongHopTon(lots) {
  const totals = new Map();
  for (const lot of lots) {
    const total = totals.get(lot.ma_sp) || {actual:0, reserved:0, available:0};
    total.actual += lot.ton_thuc_te;
    total.reserved += lot.dang_giu;
    total.available += lot.kha_dung;
    totals.set(lot.ma_sp, total);
  }
  return totals;
}

function hienTonTheoSanPham(lots) {
  const tbody = document.querySelector("[data-stock-overview]");
  if (!tbody) return;
  const totals = tongHopTon(lots);
  tbody.replaceChildren();
  const rows = [...products.values()].sort((a,b) => a.ten_sp.localeCompare(b.ten_sp,"vi"));
  for (const product of rows.slice(0,8)) {
    const total = totals.get(product.ma_sp) || {actual:0,reserved:0,available:0};
    const tr = tbody.insertRow();
    const title = cell(tr, product.ten_sp);
    const code = title.appendChild(document.createElement("small"));
    code.className = "subline"; code.textContent = product.ma_sp + " · " + product.don_vi_tinh;
    cell(tr, number.format(total.actual), "numeric");
    cell(tr, number.format(total.reserved), "numeric");
    const available = cell(tr, number.format(total.available), "numeric stock-available");
    const unit = available.appendChild(document.createElement("small"));
    unit.className="subline"; unit.textContent=product.don_vi_tinh;
    const link = cell(tr,"").appendChild(document.createElement("a"));
    link.href = "/kho/lo-hang?" + new URLSearchParams({ma_sp:product.ma_sp});
    link.textContent = "Xem lô"; link.className="text-link";
  }
  if (!rows.length) cell(tbody.insertRow(),"Chưa có sản phẩm được ghi nhận.","empty").colSpan=5;
}

async function dashboard(section) {
  const [lots, alerts] = await Promise.all([goiApi(api + "/lo-hang"), goiApi(api + "/canh-bao")]);
  section.querySelector("[data-lots]").textContent = number.format(lots.length);
  section.querySelector("[data-available]").textContent = number.format([...tongHopTon(lots).values()].filter(p => p.available > 0).length);
  section.querySelector("[data-low]").textContent = number.format(alerts.ton_thap.length);
  section.querySelector("[data-expiring]").textContent = number.format(alerts.sap_het_han.length);
  hienTonTheoSanPham(lots);
  section.setAttribute("aria-busy","false");
  document.querySelector("[data-dashboard-updated]").textContent = "Cập nhật lúc " + new Date().toLocaleTimeString("vi-VN");
  const preview = document.querySelector("[data-alert-preview]");
  preview.replaceChildren();
  for (const warning of [...alerts.ton_thap.slice(0,2), ...alerts.sap_het_han.slice(0,2)]) {
    const item = preview.appendChild(document.createElement("div"));
    item.className = "alert-preview";
    item.append(badge(warning.ma_lo ? "Sắp hết hạn" : "Tồn thấp", warning.ma_lo ? "danger" : "pending"));
    const title = item.appendChild(document.createElement("strong"));
    title.textContent = (products.get(warning.ma_sp)?.ten_sp || warning.ma_sp) + (warning.ma_lo ? " · " + warning.ma_lo : "");
    const action = item.appendChild(document.createElement("a"));
    action.className = "text-link"; action.textContent = "Kiểm tra lô liên quan";
    action.href = "/kho/lo-hang?" + new URLSearchParams(warning.ma_lo ? {ma_lo:warning.ma_lo}:{ma_sp:warning.ma_sp});
    const text = item.appendChild(document.createElement("p"));
    text.textContent = warning.noi_dung;
  }
  if (!preview.children.length) {
    const text = preview.appendChild(document.createElement("p"));
    text.className = "empty";
    text.textContent = "Chưa có cảnh báo cần xử lý.";
  }
}

function formPhieu(form) {
  const holder = form.querySelector("[data-rows]");
  const row = form.querySelector("[data-row-template]").content.firstElementChild.cloneNode(true);
  holder.append(row);
  const save = form.querySelector('button[type="submit"]');
  row.elements.ma_sp.addEventListener("change", () => {
    const food = row.elements.ma_sp.selectedOptions[0]?.dataset.food === "yes";
    row.elements.ngay_san_xuat.required = food;
    row.elements.han_su_dung.required = food;
  });
  form.addEventListener("input", ({ target }) => {
    target.removeAttribute("aria-invalid");
    const quantity = Number(row.elements.so_luong_nhap.value) || 0;
    const price = Number(row.elements.gia_nhap.value) || 0;
    form.querySelector("[data-receipt-total]").textContent = money(quantity * price);
  });
  let submitted = false;
  form.addEventListener("submit", async event => {
    event.preventDefault();
    if (save.disabled) return;
    hienLoi(null);
    const get = name => row.elements.namedItem(name).value;
    const dong = [{
      ma_sp: get("ma_sp"), ma_lo: get("ma_lo").trim(),
      so_luong_nhap: Number(get("so_luong_nhap")), gia_nhap: Number(get("gia_nhap")),
      ngay_san_xuat: get("ngay_san_xuat") || null, han_su_dung: get("han_su_dung") || null,
    }];
    save.disabled = true;
    save.textContent = "Đang lưu…";
    try {
      const result = await goiApi(api + "/phieu-nhap", {
        method: "POST",
        body: {ma_ncc: form.elements.ma_ncc.value, ngay_nhap: form.elements.ngay_nhap.value, dong},
      });
      submitted = true;
      location.assign(phieuPath + encodeURIComponent(result.ma_phieu));
    } catch (error) { hienLoi(error, form); }
    finally { save.disabled = false; save.textContent = "Lưu phiếu nháp"; }
  });
  let dirty = false;
  form.addEventListener("input", () => { dirty = true; });
  window.addEventListener("beforeunload", event => {
    if (dirty && !submitted) { event.preventDefault(); event.returnValue = ""; }
  });
}

async function chiTietPhieu(section) {
  const path = api + "/phieu-nhap/" + encodeURIComponent(section.dataset.receipt);
  const confirm = section.querySelector("[data-confirm]");
  const feedback = section.querySelector("[data-feedback]");
  function show(receipt) {
    const completed = receipt.trang_thai === "DA_XAC_NHAN";
    const status = section.querySelector("[data-status]");
    status.textContent = completed ? "Đã xác nhận" : "Nháp";
    status.className = "badge " + (completed ? "success" : "pending");
    section.querySelector("[data-supplier]").textContent = suppliers.get(receipt.ma_ncc) || receipt.ma_ncc;
    section.querySelector("[data-date]").textContent = dateText(receipt.ngay_nhap);
    section.querySelector("[data-employee]").textContent = receipt.ma_nv;
    const tbody = section.querySelector("tbody");
    tbody.replaceChildren();
    for (const item of receipt.dong) {
      const tr = tbody.insertRow();
      const productCell = cell(tr, products.get(item.ma_sp)?.ten_sp || item.ma_sp);
      const code = productCell.appendChild(document.createElement("small"));
      code.className = "subline"; code.textContent = item.ma_sp;
      cell(tr, item.ma_lo);
      cell(tr, number.format(item.so_luong_nhap), "numeric");
      cell(tr, money(item.gia_nhap), "numeric nowrap");
      cell(tr, dateText(item.ngay_san_xuat), "nowrap");
      cell(tr, dateText(item.han_su_dung), "nowrap");
    }
    section.querySelector("[data-total]").textContent = money(receipt.dong.reduce((sum,p)=>sum+p.gia_nhap*p.so_luong_nhap,0));
    confirm.hidden = completed;
    section.querySelector("[data-details]").hidden = false;
    document.querySelector("[data-print]").disabled = false;
  }
  try { show(await goiApi(path)); }
  finally { section.querySelector("[data-loading]").hidden = true; }
  confirm.addEventListener("click", async () => {
    if (confirm.disabled) return;
    hienLoi(null); confirm.disabled = true; confirm.textContent = "Đang xác nhận…";
    try {
      show(await goiApi(path + "/xac-nhan", {method: "POST", body: {}}));
      feedback.textContent = "Đã xác nhận phiếu. Tồn kho đã được cập nhật.";
      feedback.hidden = false;
    } catch (error) { hienLoi(error); }
    finally { confirm.disabled = false; confirm.textContent = "Xác nhận nhập kho"; }
  });
}

async function danhSachLo(section) {
  const form = section.querySelector("form");
  const summary = section.querySelector("[data-lot-summary]");
  const tbody = section.querySelector("tbody");
  const params = new URLSearchParams(location.search);
  form.elements.q.value = params.get("q") || params.get("ma_lo") || params.get("ma_sp") || "";
  form.elements.tinh_trang.value = params.get("tinh_trang") || "";
  const lots = await goiApi(api + "/lo-hang");
  const searchIndex = new Map(lots.map(item => [item.ma_lo, normalize(
    [item.ma_lo,item.ma_sp,products.get(item.ma_sp)?.ten_sp,catalog.nha_cung_cap_theo_lo?.[item.ma_lo]].join(" ")
  )]));
  const exactProduct = params.get("ma_sp");
  const exactLot = params.get("ma_lo");
  let page = 1;
  let result = [];
  const perPage = 10;
  function render() {
    tbody.replaceChildren();
    for (const item of result.slice((page-1)*perPage, page*perPage)) {
      const tr = tbody.insertRow();
      const lot = cell(tr, item.ma_lo, "nowrap");
      const entered = lot.appendChild(document.createElement("small"));
      entered.className = "subline"; entered.textContent = "Nhập " + dateText(item.ngay_nhap);
      const product = cell(tr, products.get(item.ma_sp)?.ten_sp || item.ma_sp);
      const code = product.appendChild(document.createElement("small"));
      code.className = "subline"; code.textContent = item.ma_sp;
      cell(tr, catalog.nha_cung_cap_theo_lo?.[item.ma_lo] || "Chưa ghi nhận");
      const expiry = cell(tr, dateText(item.han_su_dung), "nowrap");
      if (item.ngay_san_xuat) {
        const made = expiry.appendChild(document.createElement("small"));
        made.className = "subline"; made.textContent = "SX " + dateText(item.ngay_san_xuat);
      }
      cell(tr, number.format(item.ton_thuc_te), "numeric");
      cell(tr, number.format(item.dang_giu), "numeric");
      cell(tr, number.format(item.kha_dung), "numeric");
      const [label, style] = lotStatus(item);
      cell(tr, "").append(badge(label, style));
    }
    if (!result.length) cell(tbody.insertRow(), "Không có lô hàng phù hợp.").colSpan = 8;
    const totalPages = Math.max(1, Math.ceil(result.length / perPage));
    section.querySelector("[data-page]").textContent = page + " / " + totalPages;
    section.querySelector("[data-prev]").disabled = page === 1;
    section.querySelector("[data-next]").disabled = page === totalPages;
    summary.textContent = result.length ? (page-1)*perPage+1 + "–" + Math.min(page*perPage,result.length) + " trên " + result.length + " lô hàng" : "Không tìm thấy lô hàng";
  }
  function filter() {
    const term = normalize(form.elements.q.value);
    const status = form.elements.tinh_trang.value;
    result = lots.filter(item => {
      const matches = exactProduct && term === normalize(exactProduct) ? item.ma_sp === exactProduct :
        exactLot && term === normalize(exactLot) ? item.ma_lo === exactLot : searchIndex.get(item.ma_lo).includes(term);
      return matches && (!status || lotStatus(item)[2]===status);
    });
    page = 1;
    const query = new URLSearchParams();
    if (exactProduct && term === normalize(exactProduct)) query.set("ma_sp",exactProduct);
    else if (exactLot && term === normalize(exactLot)) query.set("ma_lo",exactLot);
    else if (form.elements.q.value.trim()) query.set("q",form.elements.q.value.trim());
    if (status) query.set("tinh_trang",status);
    history.replaceState(null,"",location.pathname+(query.size ? "?"+query : ""));
    render();
  }
  form.addEventListener("submit",event=>{event.preventDefault();filter();});
  form.elements.q.addEventListener("input",filter);
  form.elements.tinh_trang.addEventListener("change",filter);
  form.addEventListener("reset",()=>setTimeout(filter,0));
  section.querySelector("[data-prev]").addEventListener("click",()=>{page--;render();});
  section.querySelector("[data-next]").addEventListener("click",()=>{page++;render();});
  filter();
}

async function danhSachCanhBao(section) {
  const groups = [
    ["[data-low-list]", "ton_thap", "[data-low-count]", "Không có sản phẩm dưới ngưỡng."],
    ["[data-expiring-list]", "sap_het_han", "[data-expiring-count]", "Không có lô sắp hết hạn."],
  ];
  const result = await goiApi(api + "/canh-bao");
  for (const [selector, key, count, empty] of groups) {
    const list = section.querySelector(selector);
    list.replaceChildren();
    section.querySelector(count).textContent = result[key].length;
    if (!result[key].length) {
      const item = list.appendChild(document.createElement("li"));
      item.textContent = empty; item.className = "empty"; continue;
    }
    for (const warning of result[key]) {
      const item = list.appendChild(document.createElement("li"));
      const link = item.appendChild(document.createElement("a"));
      link.href = "/kho/lo-hang?" + new URLSearchParams(warning.ma_lo ? {ma_lo:warning.ma_lo}:{ma_sp:warning.ma_sp});
      link.textContent = products.get(warning.ma_sp)?.ten_sp || warning.ma_sp;
      const text = item.appendChild(document.createElement("span"));
      text.textContent = warning.noi_dung + (warning.han_su_dung ? " · " + dateText(warning.han_su_dung) : "");
    }
  }
}

async function danhSachSanPham(section) {
  const search = section.querySelector("[data-product-search]");
  const status = section.querySelector("[data-product-status]");
  const category = section.querySelector("[data-product-category]");
  const rows = [...section.querySelectorAll("[data-product-row]")];
  function filter() {
    let count = 0;
    for (const row of rows) {
      row.hidden = !normalize(row.dataset.search).includes(normalize(search.value))
        || Boolean(category.value && category.value !== row.dataset.category)
        || Boolean(status.value && status.value !== row.dataset.status);
      if (!row.hidden) count++;
    }
    section.querySelector("[data-products-empty]").hidden = count > 0;
    section.querySelector("[data-product-count]").textContent = count + " sản phẩm";
  }
  search.addEventListener("input",filter);
  status.addEventListener("change",filter);
  category.addEventListener("change",filter);
  filter();
  const totals = tongHopTon(await goiApi(api + "/lo-hang"));
  for (const row of rows) row.querySelector("[data-product-available]").textContent = number.format(totals.get(row.dataset.code)?.available || 0);
}

document.querySelector("[data-dashboard-refresh]")?.addEventListener("click",async event=>{
  const button = event.currentTarget;
  if(button.disabled) return;
  button.disabled=true; button.textContent="Đang cập nhật…";
  hienLoi(null);
  try { await dashboard(document.querySelector("[data-dashboard]")); }
  catch(error){hienLoi(error);}
  finally {button.disabled=false;button.textContent="Làm mới số liệu";}
});
document.querySelector("[data-print]")?.addEventListener("click",()=>window.print());

for (const [selector, init] of [
  ["[data-dashboard]",dashboard],["[data-receipt-form]",formPhieu],
  ["[data-receipt]",chiTietPhieu],["[data-lot-list]",danhSachLo],
  ["[data-alert-list]",danhSachCanhBao],["[data-product-list]",danhSachSanPham],
]) {
  const section = document.querySelector(selector);
  if (section) Promise.resolve().then(()=>init(section)).catch(error=>hienLoi(error));
}
