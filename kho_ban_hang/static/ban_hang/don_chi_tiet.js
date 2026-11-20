Api.khoiTao({batBuoc:"NV_BAN_HANG"}).then(()=>{
  const goc=document.getElementById("trang"), ma=goc.dataset.maDon, code=encodeURIComponent(ma);
  const $=id=>document.getElementById(id), loi=$("loi"), url="/api/ban-hang/don-hang/"+code;
  let busy=false, amount=null;
  function xoaLoi(){loi.hidden=true;goc.querySelectorAll(".loi-truong").forEach(node=>node.textContent="");}
  function hienLoi(error){
    const field=[...goc.querySelectorAll("[data-loi-truong]")].find(node=>node.dataset.loiTruong===error.truong);
    const text=error.thong_bao||error.message||"Không thực hiện được yêu cầu. Vui lòng thử lại.";
    if(field){field.textContent=text;field.closest("label")?.querySelector("input,select")?.focus();}
    else{loi.textContent=text;loi.hidden=false;loi.setAttribute("tabindex","-1");loi.focus();}
  }
  function ve(d){
    $("ma-don").textContent=d.ma_don;
    const status=$("trang-thai");
    status.textContent={CHO_THANH_TOAN:"Chờ thanh toán",DA_THANH_TOAN:"Đã thanh toán",DA_HUY:"Đã hủy"}[d.trang_thai]||d.trang_thai;
    status.className="badge "+(d.trang_thai==="DA_THANH_TOAN"?"success":d.trang_thai==="DA_HUY"?"danger":"warning");
    $("khach-hang-info").hidden=false;
    if(!d.ten_kh){$("ten-kh").textContent="Khách lẻ";$("ma-kh").textContent="";$("badge-vip").hidden=true;}
    if(d.ten_kh){$("ten-kh").textContent=d.ten_kh;$("ma-kh").textContent=d.ma_kh||"";$("badge-vip").hidden=d.hang_kh!=="VIP";}
    for(const [id,value] of [["tam-tinh",d.tam_tinh],["giam-khach",d.giam_hang_khach],["giam-km",d.giam_khuyen_mai],["phai-tra",d.so_phai_tra]])$(id).textContent=Api.tien(value);
    const body=$("chi-tiet-don-body");
    if(body){
      body.replaceChildren();
      for(const item of d.dong || []){
        const row=body.insertRow();
        for(const [i,text] of [item.ten_sp||item.ma_sp,item.so_luong+" "+(item.don_vi_tinh||""),Api.tien(item.don_gia),Api.tien(item.thanh_tien)].entries()){
          const cell=row.insertCell();cell.textContent=text;if(i)cell.className="so";
        }
      }
      $("chi-tiet-don").hidden=false;
    }
    amount=d.so_phai_tra;$("tong-hop").hidden=false;
    const rounded=Math.ceil((amount+1)/100000)*100000;
    for(const button of goc.querySelectorAll("[data-cash]")){
      const value=button.dataset.cash==="exact"?amount:button.dataset.cash==="round"?rounded:Math.max(rounded+100000,Math.ceil((amount+1)/500000)*500000);
      button.dataset.amount=String(value);button.textContent=button.dataset.cash==="exact"?"Vừa đủ":Api.tien(value);
    }
    const pending=d.trang_thai==="CHO_THANH_TOAN";
    $("khu-km").hidden=$("khu-thanh-toan").hidden=$("nut-huy").hidden=!pending;
    $("lien-ket-hoa-don").hidden=d.trang_thai!=="DA_THANH_TOAN";
    $("lien-ket-hoa-don").href="/ban-hang/don-hang/"+code+"/hoa-don";
    capNhatTien();
  }
  async function thaoTac(action,source){
    if(busy)return;
    busy=true;xoaLoi();goc.setAttribute("aria-busy","true");
    const buttons=[...goc.querySelectorAll("button")].map(button=>[button,button.disabled]);
    const original=source?.textContent;buttons.forEach(([button])=>button.disabled=true);
    if(source)source.textContent="Đang xử lý…";
    try{await action();}catch(error){hienLoi(error);}
    finally{busy=false;goc.setAttribute("aria-busy","false");buttons.forEach(([button,disabled])=>button.disabled=disabled);if(source)source.textContent=original;}
  }
  const form=$("form-tt");
  function capNhatTien(){
    const text=$("du-kien-tien-thoi");if(!text)return;
    const value=form.tien_khach_dua.value.trim(),cash=Api.docTien(value);
    text.hidden=amount===null||!value||!Number.isSafeInteger(cash)||cash<0||form.phuong_thuc.value!=="TIEN_MAT";
    if(!text.hidden)text.textContent=cash<amount?"Khách còn thiếu "+Api.tien(amount-cash):"Dự kiến trả lại khách "+Api.tien(cash-amount);
  }
  form.phuong_thuc.addEventListener("change",()=>{
    const bank=form.phuong_thuc.value==="CHUYEN_KHOAN";
    $("nhom-tien-mat").hidden=bank;$("nhom-chuyen-khoan").hidden=!bank;
    if(bank && !form.so_tien_doi_soat.value && amount!==null)form.so_tien_doi_soat.value=new Intl.NumberFormat("vi-VN").format(amount);
    capNhatTien();
  });
  form.tien_khach_dua.addEventListener("input",capNhatTien);
  $("form-km").addEventListener("submit",event=>{
    event.preventDefault();
    thaoTac(async()=>ve(await Api.post(url+"/khuyen-mai",{ma_km:event.target.ma_km.value})),event.submitter);
  });
  for(const button of goc.querySelectorAll("[data-cash]"))button.addEventListener("click",()=>{
    form.tien_khach_dua.value=new Intl.NumberFormat("vi-VN").format(Number(button.dataset.amount));
    form.tien_khach_dua.dispatchEvent(new Event("input"));form.tien_khach_dua.focus();
  });
  const number=value=>Api.docTien(value);
  form.addEventListener("submit",event=>{
    event.preventDefault();
    const bank=form.phuong_thuc.value==="CHUYEN_KHOAN";
    const amountField=bank?form.so_tien_doi_soat:form.tien_khach_dua;
    const entered=number(amountField.value);
    if(entered===null || !Number.isSafeInteger(entered)){
      hienLoi({truong:bank?"thong_tin.so_tien_doi_soat":"thong_tin.tien_khach_dua",thong_bao:"Nhập số tiền hợp lệ, ví dụ 500.000."});return;
    }
    const thong_tin=bank?{so_tien_doi_soat:number(form.so_tien_doi_soat.value),ten_ngan_hang:form.ten_ngan_hang.value,ma_giao_dich_ngan_hang:form.ma_giao_dich_ngan_hang.value}:{tien_khach_dua:number(form.tien_khach_dua.value)};
    thaoTac(async()=>{
      await Api.post(url+"/thanh-toan",{phuong_thuc:form.phuong_thuc.value,thong_tin});
      location.assign("/ban-hang/don-hang/"+code+"/hoa-don");
    },event.submitter);
  });
  $("nut-huy").addEventListener("click",event=>{
    if(busy||!confirm("Hủy đơn "+ma+"? Hàng đang giữ sẽ được hoàn lại."))return;
    thaoTac(async()=>{await Api.post(url+"/huy",{});ve(await Api.get(url));},event.currentTarget);
  });
  thaoTac(async()=>ve(await Api.get(url)));
}).catch(error=>Api.hienLoiPhien(error));
