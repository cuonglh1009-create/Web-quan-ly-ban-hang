Api.khoiTao({ batBuoc: "NV_BAN_HANG" }).then(async () => {
  const goc = document.getElementById("trang"), ma = encodeURIComponent(goc.dataset.maDon),
        $ = (id) => document.getElementById(id);
  $("ve-don").href = "/ban-hang/don-hang/" + ma;
  try {
    const d = await Api.get("/api/ban-hang/don-hang/" + ma + "/hoa-don");
    $("ma-hd").textContent = d.ma_hd; $("ma-don").textContent = d.ma_don; $("ngay").textContent = d.ngay_xuat;
    $("phuong-thuc").textContent = d.phuong_thuc === "TIEN_MAT" ? "Tiền mặt" : "Chuyển khoản";
    const tb = $("dong");
    for (const r of d.dong) {
      const tr = document.createElement("tr");
      const product=document.createElement("td");
      product.textContent=r.ten_sp || r.ma_sp;
      const code=document.createElement("small");code.className="subline";code.textContent=r.ma_sp;product.append(code);tr.append(product);
      [String(r.so_luong)+(r.don_vi_tinh ? " "+r.don_vi_tinh : ""), Api.tien(r.don_gia), Api.tien(r.thanh_tien)].forEach(v => {
        const td=document.createElement("td");td.textContent=v;td.className="so";tr.append(td);
      });
      tb.append(tr);
    }
    $("truoc-giam").textContent = Api.tien(d.tong_tien_truoc_giam);
    $("tong-giam").textContent = Api.tien(d.tong_giam);
    $("tong-tt").textContent = Api.tien(d.tong_thanh_toan);
    if (d.tien_thoi !== null) { $("hang-tien-thoi").hidden = false; $("tien-thoi").textContent = Api.tien(d.tien_thoi); }
    $("hoa-don").hidden = false;
    const print=document.querySelector("[data-in-invoice]");print.disabled=false;print.onclick=()=>window.print();
  } catch (e) { const l = $("loi"); l.textContent = e.thong_bao; l.hidden = false; }
}).catch(error=>Api.hienLoiPhien(error));
