const Api = {
  csrf: null,
  phien: null,

  async goi(phuongThuc, url, thanBody, options = {}) {
    const tieuDe = { Accept: "application/json" };
    if (phuongThuc !== "GET") {
      tieuDe["Content-Type"] = "application/json";
      tieuDe["X-CSRF-Token"] = Api.csrf;          // gửi cho mọi POST
    }
    let r;
    try {
      r = await fetch(url, { method: phuongThuc, headers: tieuDe, credentials: "same-origin",
        signal: options.signal, body: phuongThuc === "GET" ? undefined : JSON.stringify(thanBody ?? {}) });
    } catch(error) {
      if(error.name==="AbortError")throw error;
      throw {ma_loi:"LOI_MANG",thong_bao:"Không kết nối được máy chủ. Kiểm tra kết nối rồi thử lại.",truong:null};
    }
    let d = null;
    try { d = await r.json(); } catch (_) { /* thân rỗng */ }
    if (!r.ok) {
      const loi = (d && d.loi) || { ma_loi: "LOI_MANG", thong_bao: "Không kết nối được máy chủ", truong: null };
      loi.status = r.status;
      if(r.status===401 && Api.phien?.da_dang_nhap) location.assign("/dang-nhap");
      throw loi;
    }
    if(!d || !Object.prototype.hasOwnProperty.call(d,"du_lieu"))throw {ma_loi:"PHAN_HOI_KHONG_HOP_LE",thong_bao:"Máy chủ trả dữ liệu không hợp lệ. Vui lòng thử lại.",truong:null};
    return d.du_lieu;
  },
  get(url, options) { return Api.goi("GET", url, undefined, options); },
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
    if (!p.da_dang_nhap) { if(ten)ten.textContent = ""; if(nut)nut.hidden = true; return; }
    if (menu) {
      const muc = p.nguoi_dung.vai_tro === "NV_KHO"
        ? [["/kho", "Kho"]]
        : [
            ["/ban-hang/don-hang/moi", "Lập đơn mới"],
            ["/ban-hang/don-hang", "Đơn hàng"],
            ["/ban-hang/khach-hang", "Khách hàng"],
            ["/ban-hang/thong-ke", "Thống kê"],
            ["/ban-hang/tra-cuu-kho", "Tra cứu kho"],
          ];
      for (const [href, nhan] of muc) {
        const a = document.createElement("a"); a.href = href; a.textContent = nhan;
        if (location.pathname === href || (href === "/ban-hang/don-hang" && location.pathname === "/ban-hang")) {
          a.setAttribute("aria-current", "page");
        }
        menu.append(a);
      }
    }
    if(ten)ten.textContent = p.nguoi_dung.ho_ten;
    if(!nut)return;
    nut.hidden = false;
    nut.onclick = async () => {
      if(nut.disabled)return;
      nut.disabled=true;
      try {const kq=await Api.post("/api/xac-thuc/dang-xuat",{});location.href=kq.trang_chu;}
      catch(error){Api.hienLoiPhien(error);}
      finally{nut.disabled=false;}
    };
  },

  hienLoiPhien(error) {
    const main=document.querySelector("#main");
    if(!main)return;
    let notice=main.querySelector("[data-session-error]");
    if(!notice){notice=document.createElement("div");notice.className="notice";notice.dataset.sessionError="";notice.setAttribute("role","alert");main.prepend(notice);}
    notice.replaceChildren();
    const text=document.createElement("p");
    const internal=error instanceof TypeError || error instanceof ReferenceError;
    if(internal)console.error("Không khởi tạo được giao diện:",error);
    text.textContent=internal?"Không tải được giao diện. Hãy tải lại trang để cập nhật.":(error.thong_bao||error.message||"Không tải được phiên làm việc.");
    const retry=document.createElement("button");retry.type="button";retry.className="secondary";retry.textContent="Tải lại trang";retry.onclick=()=>location.reload();
    notice.append(text,retry);
  },

  taoPhanTrang(tbody, onPage) {
    const footer=document.createElement("div");footer.className="table-footer";
    const status=document.createElement("span");status.setAttribute("role","status");
    const controls=document.createElement("div");controls.className="pagination";
    const prev=document.createElement("button"),next=document.createElement("button");
    prev.type=next.type="button";prev.className=next.className="secondary";
    prev.textContent="Trang trước";next.textContent="Trang sau";
    const label=document.createElement("label");label.className="page-size-label";label.textContent="Số dòng/trang";
    const size=document.createElement("select");
    for(const value of [10,20,50,100]){const option=document.createElement("option");option.value=value;option.textContent=value;size.append(option);}
    const query=new URLSearchParams(location.search);
    size.value=["10","20","50","100"].includes(query.get("page_size"))?query.get("page_size"):"20";
    label.append(size);controls.append(label,prev,next);footer.append(status,controls);
    tbody.closest(".table-wrap").after(footer);
    let page=1,pages=1;
    function load(target){prev.disabled=next.disabled=true;status.textContent="Đang tải…";onPage(target);}
    prev.onclick=()=>load(page-1);next.onclick=()=>load(page+1);size.onchange=()=>load(1);
    prev.disabled=next.disabled=true;
    return {
      initialPage:Math.max(1,Number(query.get("page"))||1),
      url(url, target=1){
        const parsed=new URL(url,location.origin);parsed.searchParams.set("page",target);parsed.searchParams.set("page_size",size.value);
        history.replaceState(null,"",location.pathname+"?"+parsed.searchParams);
        return parsed.pathname+parsed.search;
      },
      render(result){
        if(Array.isArray(result))result={items:result,total:result.length,page:1,pages:1,page_size:Number(size.value)};
        page=result.page;pages=result.pages;
        const actual=new URL(location.href);actual.searchParams.set("page",page);actual.searchParams.set("page_size",result.page_size);history.replaceState(null,"",actual.pathname+actual.search);
        prev.disabled=page<=1;next.disabled=page>=pages;
        status.textContent=result.total ? ((page-1)*result.page_size+1)+"–"+Math.min(page*result.page_size,result.total)+" / "+result.total+" · Trang "+page+"/"+pages : "Không có kết quả";
      },
      error(){prev.disabled=next.disabled=true;status.textContent="Không tải được trang. Hãy thử tìm lại.";}
    };
  },

  docTien(value) {
    const raw=String(value ?? "").trim().replace(/[\u00a0\u202f]/g," ");
    if(!raw)return null;
    if(!/^\d+$/.test(raw) && !/^\d{1,3}([., ])\d{3}(?:\1\d{3})*$/.test(raw))return NaN;
    const number=Number(raw.replace(/[., ]/g,""));
    return Number.isSafeInteger(number) && number>=0 ? number : NaN;
  },

  html(value) {
    return String(value ?? "").replace(/[&<>"\']/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","\'":"&#39;"}[char]));
  },

  tien(n) { return new Intl.NumberFormat("vi-VN").format(n) + " đ"; },
};
