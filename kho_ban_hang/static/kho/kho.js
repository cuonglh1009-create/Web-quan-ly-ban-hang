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

function hienThi(selector, value, root=document) {
  const element=root.querySelector(selector);
  if(element)element.textContent=value;
}

function hienLoi(loi, form) {
  const notice = document.querySelector("[data-error]");
  if (!notice) return;
  notice.hidden = !loi;
  const internal=loi instanceof TypeError || loi instanceof ReferenceError;
  if(internal)console.error("Không khởi tạo được một thành phần giao diện kho:",loi);
  notice.textContent = !loi ? "" : internal ? "Một phần giao diện chưa tải được. Hãy tải lại trang để cập nhật." : (loi.message || "Không thực hiện được yêu cầu. Vui lòng thử lại.");
  if (!loi) return;
  if (form && loi.truong) {
    const match = /^dong\[(\d+)\]\.(\w+)$/.exec(loi.truong);
    const field = match
      ? form.querySelectorAll("fieldset")[Number(match[1])]?.elements.namedItem(match[2])
      : form.elements.namedItem(loi.truong);
    if (field?.focus) {
      field.setAttribute("aria-invalid", "true");
      let detail=field.parentElement.querySelector("[data-field-error]");
      if(!detail){detail=document.createElement("span");detail.className="loi-truong";detail.dataset.fieldError="";detail.id="receipt-error-"+field.name;field.parentElement.append(detail);}
      detail.textContent=loi.message;field.setAttribute("aria-describedby",detail.id);
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
  if (expiry !== null && expiry < current) return ["Đã hết hạn", "neutral", "het_han"];
  if (row.ton_thuc_te === 0) return ["Hết hàng", "neutral", "het_hang"];
  if (expiry !== null && expiry <= current + catalog.so_ngay_canh_bao * 86400000) return ["Sắp hết hạn", "pending", "sap_het_han"];
  if (row.kha_dung === 0) return ["Không khả dụng", "neutral", "khong_kha_dung"];
  return ["Còn khả dụng", "success", "con_hang"];
}

function hienTonTheoSanPham(rows) {
  const tbody = document.querySelector("[data-stock-overview]");
  if (!tbody) return;
  tbody.replaceChildren();
  for (const product of rows.slice(0,8)) {
    const total = product;
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
  const alerts=await goiApi(api+"/tong-quan");
  hienThi("[data-lots]",number.format(alerts.lots),section);
  hienThi("[data-available]",number.format(alerts.available_products),section);
  hienThi("[data-low]",number.format(alerts.low_products),section);
  hienThi("[data-reserved-lots]",number.format(alerts.reserved_lots),section);
  hienTonTheoSanPham(alerts.san_pham);
  section.setAttribute("aria-busy","false");
  hienThi("[data-dashboard-updated]","Cập nhật lúc " + new Date().toLocaleTimeString("vi-VN"));
  const preview = document.querySelector("[data-alert-preview]");
  if(!preview)return;
  preview.replaceChildren();
  for (const warning of [...alerts.ton_thap.slice(0,2), ...alerts.sap_het_han.slice(0,2)]) {
    const item = preview.appendChild(document.createElement("div"));
    item.className = "alert-preview";
    item.append(badge(warning.ma_lo ? "Sắp hết hạn" : "Tồn thấp", warning.ma_lo ? "neutral" : "pending"));
    const title = item.appendChild(document.createElement("strong"));
    title.textContent = (warning.ten_sp || products.get(warning.ma_sp)?.ten_sp || warning.ma_sp) + (warning.ma_lo ? " · " + warning.ma_lo : "");
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
    const detail=target.parentElement.querySelector("[data-field-error]");
    if(detail)detail.textContent="";
    const quantity = Number(row.elements.so_luong_nhap.value) || 0;
    const price = Api.docTien(row.elements.gia_nhap.value) || 0;
    row.elements.gia_nhap.setCustomValidity("");
    form.querySelector("[data-receipt-total]").textContent = money(quantity * price);
  });
  let submitted = false;
  form.addEventListener("submit", async event => {
    event.preventDefault();
    if (save.disabled) return;
    hienLoi(null);
    const get = name => row.elements.namedItem(name).value;
    const price=Api.docTien(get("gia_nhap"));
    if(!Number.isSafeInteger(price)||price<=0){row.elements.gia_nhap.setCustomValidity("Nhập giá hợp lệ, ví dụ 135.000");row.elements.gia_nhap.reportValidity();return;}
    const dong = [{
      ma_sp: get("ma_sp"), ma_lo: get("ma_lo").trim(),
      so_luong_nhap: Number(get("so_luong_nhap")), gia_nhap: price,
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
    const reviewStep=document.querySelector("[data-review-step]"),doneStep=document.querySelector("[data-confirm-step]");
    if(reviewStep && doneStep){reviewStep.toggleAttribute("aria-current",!completed);if(!completed)reviewStep.setAttribute("aria-current","step");doneStep.toggleAttribute("aria-current",completed);if(completed)doneStep.setAttribute("aria-current","step");}
    section.querySelector("[data-details]").hidden = false;
    const print=document.querySelector("[data-print]");if(print)print.disabled=false;
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
  const form=section.querySelector("form"),summary=section.querySelector("[data-lot-summary]"),tbody=section.querySelector("tbody");
  const params=new URLSearchParams(location.search),exactProduct=params.get("ma_sp"),exactLot=params.get("ma_lo");
  form.elements.q.value=params.get("q")||exactProduct||exactLot||"";
  form.elements.tinh_trang.value=params.get("tinh_trang")||"";
  let page=Math.max(1,Number(params.get("page"))||1),result=[],meta=null,request=null,timer;
  const perPage=10,prev=section.querySelector("[data-prev]"),next=section.querySelector("[data-next]");
  function render(){
    tbody.replaceChildren();
    for (const item of result) {
      const tr = tbody.insertRow();
      const lot = cell(tr, item.ma_lo, "nowrap");
      const entered = lot.appendChild(document.createElement("small"));
      entered.className = "subline"; entered.textContent = "Nhập " + dateText(item.ngay_nhap);
      const product = cell(tr, item.ten_sp || products.get(item.ma_sp)?.ten_sp || item.ma_sp);
      const code = product.appendChild(document.createElement("small"));
      code.className = "subline"; code.textContent = item.ma_sp;
      cell(tr, item.nha_cung_cap || "Chưa ghi nhận");
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

    if(!result.length)cell(tbody.insertRow(),"Không có lô hàng phù hợp.","empty").colSpan=8;
    page=meta.page;
    const actual=new URL(location.href);actual.searchParams.set("page",page);history.replaceState(null,"",actual.pathname+actual.search);
    section.querySelector("[data-page]").textContent=page+" / "+meta.pages;
    prev.disabled=page<=1;next.disabled=page>=meta.pages;
    summary.textContent=meta.total?((page-1)*perPage+1)+"–"+Math.min(page*perPage,meta.total)+" trên "+meta.total+" lô hàng":"Không tìm thấy lô hàng";
  }
  async function load(target=1){
    clearTimeout(timer);request?.abort();const active=new AbortController();request=active;
    const query=new URLSearchParams(),term=form.elements.q.value.trim();
    if(exactProduct && normalize(term)===normalize(exactProduct))query.set("ma_sp",exactProduct);
    else if(exactLot && normalize(term)===normalize(exactLot))query.set("ma_lo",exactLot);
    else if(term)query.set("q",term);
    if(form.elements.tinh_trang.value)query.set("tinh_trang",form.elements.tinh_trang.value);
    query.set("page",target);query.set("page_size",perPage);
    history.replaceState(null,"",location.pathname+"?"+query);
    prev.disabled=next.disabled=true;tbody.replaceChildren();cell(tbody.insertRow(),"Đang tải lô hàng…","empty").colSpan=8;
    section.setAttribute("aria-busy","true");hienLoi(null);
    try{
      const response=await goiApi(api+"/lo-hang?"+query,{signal:active.signal});
      if(active.signal.aborted)return;
      meta=Array.isArray(response)?{items:response,total:response.length,page:1,pages:1}:response;
      result=meta.items;render();
    }catch(error){
      if(active.signal.aborted || error.name==="AbortError")return;
      hienLoi(error);tbody.replaceChildren();cell(tbody.insertRow(),"Không tải được dữ liệu. Hãy bấm Tìm kiếm để thử lại.","empty").colSpan=8;summary.textContent="Chưa tải được dữ liệu";
    }finally{if(!active.signal.aborted)section.setAttribute("aria-busy","false");}
  }
  form.addEventListener("submit",event=>{event.preventDefault();load();});
  form.elements.q.addEventListener("input",()=>{clearTimeout(timer);timer=setTimeout(()=>load(),250);});
  form.elements.tinh_trang.addEventListener("change",()=>load());
  form.addEventListener("reset",()=>setTimeout(()=>load(),0));
  prev.addEventListener("click",()=>load(page-1));next.addEventListener("click",()=>load(page+1));
  await load(page);
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
  const totals = new Map((await goiApi(api + "/ton-san-pham")).map(row=>[row.ma_sp,row]));
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
