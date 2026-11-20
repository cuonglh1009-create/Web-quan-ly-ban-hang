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
    $("khach-hang-info").hidden=!d.ten_kh;
    if(d.ten_kh){$("ten-kh").textContent=d.ten_kh;$("ma-kh").textContent=d.ma_kh||"";$("badge-vip").hidden=d.hang_kh!=="VIP";}
    for(const [id,value] of [["tam-tinh",d.tam_tinh],["giam-khach",d.giam_hang_khach],["giam-km",d.giam_khuyen_mai],["phai-tra",d.so_phai_tra]])$(id).textContent=Api.tien(value);
    amount=d.so_phai_tra;$("tong-hop").hidden=false;
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
    const value=form.tien_khach_dua.value.trim(),cash=Number(value);
    text.hidden=amount===null||!value||!Number.isSafeInteger(cash)||cash<0||form.phuong_thuc.value!=="TIEN_MAT";
    if(!text.hidden)text.textContent=cash<amount?"Khách còn thiếu "+Api.tien(amount-cash):"Dự kiến trả lại khách "+Api.tien(cash-amount);
  }
  form.phuong_thuc.addEventListener("change",()=>{
    const bank=form.phuong_thuc.value==="CHUYEN_KHOAN";
    $("nhom-tien-mat").hidden=bank;$("nhom-chuyen-khoan").hidden=!bank;capNhatTien();
  });
  form.tien_khach_dua.addEventListener("input",capNhatTien);
  $("form-km").addEventListener("submit",event=>{
    event.preventDefault();
    thaoTac(async()=>ve(await Api.post(url+"/khuyen-mai",{ma_km:event.target.ma_km.value})),event.submitter);
  });
  const number=value=>value.trim()===""?null:Number(value);
  form.addEventListener("submit",event=>{
    event.preventDefault();
    const bank=form.phuong_thuc.value==="CHUYEN_KHOAN";
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
