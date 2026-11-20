Api.khoiTao({ batBuoc: "NV_BAN_HANG" }).then(async (phien) => {
  const form = document.getElementById("form-don"),
        tbody = document.getElementById("dong"),
        dongTrong = document.getElementById("dong-trong"),
        loi = document.getElementById("loi"),
        gui = document.getElementById("gui"),
        maDonEl = document.getElementById("ma-don-du-kien"),
        maKhTuDongEl = document.getElementById("ma-kh-tu-dong"),
        tenNhanVienEl = document.getElementById("ten-nhan-vien"),
        nutBatThemKh = document.getElementById("nut-bat-them-kh"),
        khoiThemKhachNhanh = document.getElementById("khoi-them-khach-nhanh"),
        nutDongThemNhanh = document.getElementById("nut-dong-them-nhanh"),
        nutHuyThemNhanh = document.getElementById("nut-huy-them-nhanh"),
        nutLuuKhachNhanh = document.getElementById("nut-luu-khach-nhanh"),
        tenKhMoiInput = document.getElementById("ten-kh-moi"),
        sdtKhMoiInput = document.getElementById("sdt-kh-moi"),
        diaChiKhMoiInput = document.getElementById("dia-chi-kh-moi"),
        chonKhachCuSelect = document.getElementById("chon-khach-cu"),
        nhapTimKhachInput = document.getElementById("nhap-tim-khach"),
        hopGoiYKhach = document.getElementById("hop-goi-y-khach"),
        danhSachGoiYKhach = document.getElementById("danh-sach-goi-y-khach"),
        dongTaoNhanhTuGoiY = document.getElementById("dong-tao-nhanh-tu-goi-y"),
        thongTinKhEl = document.getElementById("thong-tin-kh-da-chon"),
        tenKhHienThi = document.getElementById("ten-kh-hien-thi"),
        maKhHienThi = document.getElementById("ma-kh-hien-thi"),
        sdtKhHienThi = document.getElementById("sdt-kh-hien-thi"),
        hangKhHienThi = document.getElementById("hang-kh-hien-thi"),
        khChietKhauBadge = document.getElementById("kh-chiet-khau-badge"),
        nutBoChonKh = document.getElementById("nut-bo-chon-kh"),
        canhBaoTrungKhach = document.getElementById("canh-bao-trung-khach"),
        noiDungTrungKhach = document.getElementById("noi-dung-trung-khach"),
        nutDungKhachTrung = document.getElementById("nut-dung-khach-trung"),
        chonSpSelect = document.getElementById("chon-sp-nhanh"),
        soLuongInput = document.getElementById("so-luong-nhanh"),
        nutGiamSl = document.getElementById("nut-giam-sl"),
        nutTangSl = document.getElementById("nut-tang-sl"),
        nutThemSp = document.getElementById("nut-them-san-pham"),
        nutLamMoiKho = document.getElementById("nut-lam-moi-kho"),
        thoiGianDongBo = document.getElementById("thoi-gian-dong-bo"),
        chiTietSpChon = document.getElementById("chi-tiet-sp-chon"),
        ctTenSp = document.getElementById("ct-ten-sp"),
        ctMaSp = document.getElementById("ct-ma-sp"),
        ctDvt = document.getElementById("ct-dvt"),
        ctDonGia = document.getElementById("ct-don-gia"),
        ctTonKho = document.getElementById("ct-ton-kho"),
        ctBadgeTon = document.getElementById("ct-badge-ton"),
        ctNcc = document.getElementById("ct-ncc"),
        danhMucNhanhEl = document.getElementById("danh-muc-nhanh"),
        tamTinhEl = document.getElementById("hien-thi-tam-tinh"),
        giamVipEl = document.getElementById("hien-thi-giam-vip"),
        hangChietKhauVip = document.getElementById("hang-chiet-khau-vip"),
        phaiTraEl = document.getElementById("hien-thi-phai-tra");

  if (phien && phien.nguoi_dung) {
    tenNhanVienEl.value = phien.nguoi_dung.ho_ten;
  }

  // Dữ liệu đồng bộ trực tiếp từ phân hệ kho & bán hàng
  let khoSanPhams = [];
  let danhSachKhach = [];
  let khachChon = null;
  const cacDongHang = []; // { ma_sp, ten_sp, don_vi_tinh, don_gia, so_luong, so_kha_dung, nha_cung_cap }

  // 1. Tải và đồng bộ dữ liệu kho & khách hàng
  async function dongBoDuLieuKho(thongBao = false) {
    if(nutLamMoiKho.disabled)return;
    const selected=chonSpSelect.value;
    nutLamMoiKho.disabled=true;
    try {
      if (thoiGianDongBo) thoiGianDongBo.textContent = "Đang đồng bộ từ kho...";
      const spData = await Api.get("/api/ban-hang/san-pham-goi-y");
      if (Array.isArray(spData)) {
        khoSanPhams = spData;
        capNhatDropdownSanPham(spData);
        capNhatDanhMucNhanh(spData);
        if(spData.some(sp=>sp.ma_sp===selected))chonSpSelect.value=selected;
        const byCode=new Map(spData.map(sp=>[sp.ma_sp,sp]));
        for(const dong of cacDongHang){
          const current=byCode.get(dong.ma_sp);
          dong.so_kha_dung=current?.so_kha_dung||0;
          if(current)dong.don_gia=current.gia_niem_yet;
        }
        capNhatBang();
        if(chonSpSelect.value)hienThiChiTietSanPhamChon(chonSpSelect.value);
      }
      const now = new Date();
      const gio = String(now.getHours()).padStart(2, "0") + ":" +
                  String(now.getMinutes()).padStart(2, "0") + ":" +
                  String(now.getSeconds()).padStart(2, "0");
      if (thoiGianDongBo) thoiGianDongBo.textContent = `Đồng bộ lúc ${gio}`;
      if(thongBao)loi.hidden=true;
      if(cacDongHang.some(dong=>dong.so_luong>dong.so_kha_dung)){
        loi.textContent="Tồn kho vừa thay đổi. Có mặt hàng trong đơn vượt số lượng khả dụng; hãy điều chỉnh trước khi lập đơn.";
        loi.hidden=false;
      }
    } catch (err) {
      console.error("Lỗi đồng bộ kho:", err);
      if (thoiGianDongBo) thoiGianDongBo.textContent = "Chưa đồng bộ được";
      loi.textContent=err.thong_bao||"Không tải được tồn kho. Bấm đồng bộ lại để thử lại.";loi.hidden=false;
    } finally {nutLamMoiKho.disabled=false;}
  }

  async function khoiTao() {
    try {
      const [maData, khData] = await Promise.all([
        Api.get("/api/ban-hang/ma-khoi-tao"),
        Api.get("/api/ban-hang/khach-hang")
      ]);

      if (maData) {
        maDonEl.value = maData.ma_don_du_kien || "";
        maKhTuDongEl.value = maData.ma_kh_du_kien || "";
      }

      if (Array.isArray(khData)) {
        danhSachKhach = khData;
        capNhatDropdownKhachHang(khData);
      }

      await dongBoDuLieuKho();

      // Kiểm tra nếu có sản phẩm được chọn từ trang Tra cứu kho
      const maSpLuu = sessionStorage.getItem("chon_san_pham_ma");
      if (maSpLuu) {
        sessionStorage.removeItem("chon_san_pham_ma");
        chonSpSelect.value = maSpLuu;
        hienThiChiTietSanPhamChon(maSpLuu);
      }
    } catch (err) {
      loi.textContent=err.thong_bao||"Không tải được dữ liệu lập đơn. Hãy tải lại trang.";loi.hidden=false;
    }
  }

  nutLamMoiKho.onclick = () => dongBoDuLieuKho(true);

  // 2. Giao diện chọn & tìm kiếm khách hàng
  function capNhatDropdownKhachHang(danhSach) {
    chonKhachCuSelect.replaceChildren();
    const optMacDinh = document.createElement("option");
    optMacDinh.value = "";
    optMacDinh.textContent = "-- Bấm vào đây để chọn khách hàng --";
    chonKhachCuSelect.append(optMacDinh);

    for (const kh of danhSach) {
      const opt = document.createElement("option");
      opt.value = kh.ma_kh;
      const vipText = kh.hang === "VIP" ? " ⭐ [VIP - Giảm 10%]" : "";
      opt.textContent = `${kh.ma_kh} - ${kh.ho_ten} (${kh.so_dien_thoai || "Không có SĐT"})${vipText}`;
      chonKhachCuSelect.append(opt);
    }
  }

  // Khi chọn từ dropdown <select>
  chonKhachCuSelect.onchange = () => {
    const ma = chonKhachCuSelect.value;
    if (!ma) {
      boChonKhach();
      return;
    }
    const found = danhSachKhach.find((k) => k.ma_kh === ma);
    if (found) {
      chonKhach(found);
      nhapTimKhachInput.value = `${found.ho_ten} (${found.ma_kh})`;
    }
  };

  // Khi nhập tìm kiếm khách hàng đã có
  nhapTimKhachInput.addEventListener("input", () => {
    const tuKhoa = nhapTimKhachInput.value.trim().toLowerCase();
    if (!tuKhoa) {
      hopGoiYKhach.hidden = true;
      return;
    }

    const ketQua = danhSachKhach.filter((k) =>
      (k.ma_kh && k.ma_kh.toLowerCase().includes(tuKhoa)) ||
      (k.so_dien_thoai && k.so_dien_thoai.includes(tuKhoa)) ||
      (k.ho_ten && k.ho_ten.toLowerCase().includes(tuKhoa))
    );

    danhSachGoiYKhach.replaceChildren();
    if (ketQua.length === 0) {
      const emptyMsg = document.createElement("div");
      emptyMsg.style.cssText = "padding: .6rem .75rem; color: var(--muted); font-size: .85rem;";
      emptyMsg.textContent = `Không tìm thấy khách hàng nào khớp với "${nhapTimKhachInput.value.trim()}".`;
      danhSachGoiYKhach.append(emptyMsg);
    } else {
      for (const k of ketQua) {
        const item = document.createElement("div");
        item.style.cssText = "padding: .5rem .75rem; border-bottom: 1px solid #edf2ee; cursor: pointer; display: flex; justify-content: space-between; align-items: center; transition: background .15s;";
        item.onmouseover = () => item.style.background = "var(--accent-soft)";
        item.onmouseout = () => item.style.background = "#fff";

        const laVip = k.hang === "VIP";
        item.innerHTML = `
          <div>
            <strong>${Api.html(k.ho_ten)}</strong> (<span style="color: var(--accent); font-weight: 600;">${Api.html(k.ma_kh)}</span>)
            <span style="color: var(--muted); margin-left: .4rem; font-size: .85rem;">SĐT: ${Api.html(k.so_dien_thoai || "Chưa có")}</span>
          </div>
          <div>
            <span class="badge ${laVip ? "success" : ""}" style="font-size: .8rem;">${laVip ? "VIP ⭐ (Giảm 10%)" : "THƯỜNG"}</span>
          </div>
        `;

        item.onclick = () => {
          chonKhach(k);
          hopGoiYKhach.hidden = true;
          nhapTimKhachInput.value = `${k.ho_ten} (${k.ma_kh})`;
        };
        danhSachGoiYKhach.append(item);
      }
    }

    if (dongTaoNhanhTuGoiY) {
      dongTaoNhanhTuGoiY.textContent = `➕ Thêm khách hàng mới với "${nhapTimKhachInput.value.trim()}"`;
      dongTaoNhanhTuGoiY.hidden = false;
    }
    hopGoiYKhach.hidden = false;
  });

  // Khi bấm ra ngoài thì ẩn hộp gợi ý
  document.addEventListener("click", (e) => {
    if (!hopGoiYKhach.contains(e.target) && e.target !== nhapTimKhachInput) {
      hopGoiYKhach.hidden = true;
    }
  });

  function chonKhach(kh) {
    khachChon = kh;
    chonKhachCuSelect.value = kh.ma_kh;
    tenKhHienThi.textContent = kh.ho_ten;
    maKhHienThi.textContent = kh.ma_kh;
    sdtKhHienThi.textContent = kh.so_dien_thoai || "(Chưa có)";
    const laVip = kh.hang === "VIP";
    hangKhHienThi.textContent = laVip ? "VIP ⭐ (Giảm 10%)" : "THƯỜNG";
    hangKhHienThi.className = "badge " + (laVip ? "success" : "");
    if (khChietKhauBadge) {
      khChietKhauBadge.textContent = laVip ? "⭐ VIP Giảm 10%" : "";
    }
    thongTinKhEl.hidden = false;
    dongThemKhachNhanh();
    xoaLoi();
    tinhTien();
  }

  function boChonKhach() {
    khachChon = null;
    chonKhachCuSelect.value = "";
    nhapTimKhachInput.value = "";
    thongTinKhEl.hidden = true;
    hopGoiYKhach.hidden = true;
    tinhTien();
  }

  nutBoChonKh.onclick = boChonKhach;

  // 3. Khối thêm khách hàng mới nhanh tích hợp trực tiếp
  function moThemKhachNhanh(thongTinNhap = "") {
    khoiThemKhachNhanh.hidden = false;
    const chuoi = (thongTinNhap || "").trim();
    if (chuoi) {
      const soDienThoaiRe = /^[0-9+.\s-]{6,}$/;
      if (soDienThoaiRe.test(chuoi)) {
        sdtKhMoiInput.value = chuoi;
        tenKhMoiInput.value = "";
        tenKhMoiInput.focus();
      } else {
        tenKhMoiInput.value = chuoi;
        sdtKhMoiInput.value = "";
        sdtKhMoiInput.focus();
      }
    } else {
      tenKhMoiInput.focus();
    }
    kiemTraTrungKhachMoi();
  }

  function dongThemKhachNhanh() {
    khoiThemKhachNhanh.hidden = true;
    canhBaoTrungKhach.hidden = true;
  }

  if (nutBatThemKh) {
    nutBatThemKh.onclick = () => {
      if (khoiThemKhachNhanh.hidden) {
        moThemKhachNhanh(nhapTimKhachInput.value.trim());
      } else {
        dongThemKhachNhanh();
      }
    };
  }

  if (nutDongThemNhanh) nutDongThemNhanh.onclick = dongThemKhachNhanh;
  if (nutHuyThemNhanh) nutHuyThemNhanh.onclick = dongThemKhachNhanh;

  if (dongTaoNhanhTuGoiY) {
    dongTaoNhanhTuGoiY.onclick = () => {
      hopGoiYKhach.hidden = true;
      moThemKhachNhanh(nhapTimKhachInput.value.trim());
    };
  }

  // Phát hiện và gợi ý nếu khách hàng mới trùng SĐT hoặc Họ tên với khách đã có
  let khachTrungPhatHien = null;
  function kiemTraTrungKhachMoi() {
    const sdt = sdtKhMoiInput.value.trim().replace(/\s+/g, "");
    const ten = tenKhMoiInput.value.trim().toLowerCase();

    khachTrungPhatHien = null;
    if (sdt.length >= 8) {
      khachTrungPhatHien = danhSachKhach.find((k) =>
        k.so_dien_thoai && k.so_dien_thoai.replace(/\s+/g, "") === sdt
      );
    }
    if (!khachTrungPhatHien && ten.length >= 3) {
      khachTrungPhatHien = danhSachKhach.find((k) =>
        k.ho_ten && k.ho_ten.trim().toLowerCase() === ten
      );
    }

    if (khachTrungPhatHien) {
      canhBaoTrungKhach.hidden = false;
      const laVip = khachTrungPhatHien.hang === "VIP";
      noiDungTrungKhach.innerHTML = `
        <strong>${Api.html(khachTrungPhatHien.ho_ten)}</strong> (Mã KH: <strong>${Api.html(khachTrungPhatHien.ma_kh)}</strong>)
        - SĐT: <strong>${Api.html(khachTrungPhatHien.so_dien_thoai || "(Chưa có)")}</strong>
        - Hạng: <span class="badge ${laVip ? "success" : ""}">${laVip ? "VIP ⭐ (Giảm 10%)" : "THƯỜNG"}</span>
      `;
    } else {
      canhBaoTrungKhach.hidden = true;
    }
  }

  sdtKhMoiInput.addEventListener("input", kiemTraTrungKhachMoi);
  tenKhMoiInput.addEventListener("input", kiemTraTrungKhachMoi);

  nutDungKhachTrung.onclick = () => {
    if (khachTrungPhatHien) {
      chonKhach(khachTrungPhatHien);
      nhapTimKhachInput.value = `${khachTrungPhatHien.ho_ten} (${khachTrungPhatHien.ma_kh})`;
      dongThemKhachNhanh();
    }
  };

  if (nutLuuKhachNhanh) {
    nutLuuKhachNhanh.onclick = async () => {
      xoaLoi();
      const ho_ten = tenKhMoiInput.value.trim();
      const so_dien_thoai = sdtKhMoiInput.value.trim();
      const dia_chi = diaChiKhMoiInput.value.trim();
      const ma_kh = maKhTuDongEl.value.trim() || undefined;

      let coLoi = false;
      if (!ho_ten) {
        hienLoi({ truong: "ten_kh", thong_bao: "Vui lòng nhập họ tên khách hàng" });
        coLoi = true;
      }
      if (!so_dien_thoai) {
        hienLoi({ truong: "so_dien_thoai", thong_bao: "Vui lòng nhập số điện thoại khách hàng" });
        coLoi = true;
      }
      if (coLoi) return;

      nutLuuKhachNhanh.disabled = true;
      try {
        const res = await Api.post("/api/ban-hang/khach-hang", {
          ma_kh,
          ho_ten,
          so_dien_thoai,
          dia_chi
        });
        const khMoi = {
          ma_kh: res.ma_kh || ma_kh,
          ho_ten,
          so_dien_thoai,
          dia_chi,
          hang: "THUONG",
          tong_chi_tieu: 0
        };
        danhSachKhach.unshift(khMoi);
        capNhatDropdownKhachHang(danhSachKhach);
        chonKhach(khMoi);
        nhapTimKhachInput.value = `${khMoi.ho_ten} (${khMoi.ma_kh})`;

        tenKhMoiInput.value = "";
        sdtKhMoiInput.value = "";
        diaChiKhMoiInput.value = "";
        dongThemKhachNhanh();

        Api.get("/api/ban-hang/ma-khoi-tao").then((m) => {
          if (m && m.ma_kh_du_kien) maKhTuDongEl.value = m.ma_kh_du_kien;
        });
      } catch (err) {
        hienLoi(err);
      } finally {
        nutLuuKhachNhanh.disabled = false;
      }
    };
  }

  // 4. Giao diện chọn sản phẩm dạng <select> (CHỌN TRỰC TIẾP, KHÔNG PHẢI ĐIỀN)
  function capNhatDropdownSanPham(danhSach) {
    const giaTriHienTai = chonSpSelect.value;
    chonSpSelect.replaceChildren();

    const optMacDinh = document.createElement("option");
    optMacDinh.value = "";
    optMacDinh.textContent = "-- Bấm vào đây để chọn sản phẩm từ kho --";
    chonSpSelect.append(optMacDinh);

    for (const sp of danhSach) {
      const opt = document.createElement("option");
      opt.value = sp.ma_sp;
      const tonText = sp.so_kha_dung > 0 ? `Tồn kho: ${sp.so_kha_dung} ${sp.don_vi_tinh}` : "HẾT HÀNG";
      opt.textContent = `${sp.ma_sp} - ${sp.ten_sp} | Đơn giá: ${Api.tien(sp.gia_niem_yet)} | ${tonText} (NCC: ${sp.nha_cung_cap || "Kho"})`;
      chonSpSelect.append(opt);
    }

    if (giaTriHienTai && danhSach.some((p) => p.ma_sp === giaTriHienTai)) {
      chonSpSelect.value = giaTriHienTai;
      hienThiChiTietSanPhamChon(giaTriHienTai);
    } else {
      chiTietSpChon.hidden = true;
    }
  }

  // Danh mục chọn nhanh trực tiếp (Quick Pick Catalog)
  function capNhatDanhMucNhanh(danhSach) {
    danhMucNhanhEl.replaceChildren();
    for (const sp of danhSach) {
      const card = document.createElement("div");
      card.style.cssText = "background: #fff; border: 1px solid var(--line); border-radius: .45rem; padding: .65rem .8rem; display: flex; flex-direction: column; justify-content: space-between; gap: .3rem; transition: border-color .15s;";

      const hetHang = sp.so_kha_dung <= 0;
      card.innerHTML = `
        <div>
          <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: .3rem;">
            <strong style="font-size: .92rem; color: var(--ink);">${Api.html(sp.ten_sp)}</strong>
            <span class="badge ${hetHang ? "danger" : (sp.so_kha_dung <= 5 ? "warning" : "success")}" style="font-size: .75rem; white-space: nowrap;">
              ${hetHang ? "Hết" : "Tồn " + sp.so_kha_dung}
            </span>
          </div>
          <div style="font-size: .88rem; font-weight: 750; color: var(--accent); margin-top: .15rem;">${Api.tien(sp.gia_niem_yet)} <span style="font-size: .75rem; font-weight: 400; color: var(--muted);">/ ${Api.html(sp.don_vi_tinh)}</span></div>
          <div style="font-size: .78rem; color: var(--muted); margin-top: .2rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">NCC: ${Api.html(sp.nha_cung_cap || "Chưa ghi nhận")}</div>
        </div>
      `;

      const btnChon = document.createElement("button");
      btnChon.type = "button";
      btnChon.className = "secondary";
      btnChon.style.cssText = "margin-top: .45rem; padding: .3rem .5rem; font-size: .82rem; width: 100%; font-weight: 600;";
      btnChon.textContent = "+ Chọn vào đơn";
      btnChon.disabled = hetHang;
      btnChon.onclick = () => {
        chonSpSelect.value = sp.ma_sp;
        hienThiChiTietSanPhamChon(sp.ma_sp);
        themSanPhamVaoDon(sp, 1);
      };

      card.append(btnChon);
      danhMucNhanhEl.append(card);
    }
  }

  function hienThiChiTietSanPhamChon(maSp) {
    const sp = khoSanPhams.find((p) => p.ma_sp === maSp);
    if (!sp) {
      chiTietSpChon.hidden = true;
      return;
    }
    ctTenSp.textContent = sp.ten_sp;
    ctMaSp.textContent = sp.ma_sp;
    ctDvt.textContent = sp.don_vi_tinh;
    ctDonGia.textContent = Api.tien(sp.gia_niem_yet);
    ctTonKho.textContent = `${sp.so_kha_dung} ${sp.don_vi_tinh}`;
    ctNcc.textContent = sp.nha_cung_cap || "Nhà cung cấp An Phú";

    if (sp.so_kha_dung <= 0) {
      ctBadgeTon.textContent = "HẾT HÀNG";
      ctBadgeTon.className = "badge danger";
    } else if (sp.so_kha_dung <= 5) {
      ctBadgeTon.textContent = "Sắp hết hàng";
      ctBadgeTon.className = "badge warning";
    } else {
      ctBadgeTon.textContent = "Còn hàng";
      ctBadgeTon.className = "badge success";
    }
    chiTietSpChon.hidden = false;
  }

  chonSpSelect.onchange = () => {
    const ma = chonSpSelect.value;
    if (ma) hienThiChiTietSanPhamChon(ma);
    else chiTietSpChon.hidden = true;
  };

  // Nút tăng giảm số lượng tiện lợi
  nutGiamSl.onclick = () => {
    let sl = parseInt(soLuongInput.value, 10) || 1;
    if (sl > 1) soLuongInput.value = sl - 1;
  };
  nutTangSl.onclick = () => {
    let sl = parseInt(soLuongInput.value, 10) || 1;
    soLuongInput.value = sl + 1;
  };

  function themSanPhamVaoDon(sp, sl) {
    xoaLoi();
    if (!sp) return;
    if (!sl || sl <= 0) sl = 1;

    // Kiểm tra hàng đã có trong đơn chưa
    const daCo = cacDongHang.find((d) => d.ma_sp === sp.ma_sp);
    if (daCo) {
      daCo.so_luong += sl;
    } else {
      cacDongHang.push({
        ma_sp: sp.ma_sp,
        ten_sp: sp.ten_sp,
        don_vi_tinh: sp.don_vi_tinh,
        don_gia: sp.gia_niem_yet,
        so_luong: sl,
        so_kha_dung: sp.so_kha_dung,
        nha_cung_cap: sp.nha_cung_cap
      });
    }

    capNhatBang();
  }

  nutThemSp.onclick = () => {
    const ma = chonSpSelect.value;
    const sl = parseInt(soLuongInput.value, 10) || 1;
    if (!ma) {
      loi.textContent = "Vui lòng bấm chọn một sản phẩm từ danh sách.";
      loi.hidden = false;
      chonSpSelect.focus();
      return;
    }
    const sp = khoSanPhams.find((p) => p.ma_sp === ma);
    if (sp) {
      themSanPhamVaoDon(sp, sl);
      soLuongInput.value = "1";
    }
  };

  // 5. Render bảng danh sách sản phẩm trong đơn
  function capNhatBang() {
    tbody.replaceChildren();
    if (cacDongHang.length === 0) {
      dongTrong.hidden = false;
      tbody.append(dongTrong);
      tinhTien();
      return;
    }

    dongTrong.hidden = true;
    cacDongHang.forEach((dong, index) => {
      const tr = document.createElement("tr");

      // Mã SP
      const tdMa = document.createElement("td");
      tdMa.innerHTML = `<strong>${Api.html(dong.ma_sp)}</strong>`;

      // Tên SP
      const tdTen = document.createElement("td");
      tdTen.innerHTML = `<strong>${Api.html(dong.ten_sp)}</strong>`;

      // ĐVT
      const tdDvt = document.createElement("td");
      tdDvt.textContent = dong.don_vi_tinh;

      // Đơn giá kho
      const tdGia = document.createElement("td");
      tdGia.className = "so";
      tdGia.textContent = Api.tien(dong.don_gia);

      // Số lượng
      const tdSl = document.createElement("td");
      tdSl.className = "so";
      const wrapSl = document.createElement("div");
      wrapSl.style.cssText = "display: flex; align-items: center; justify-content: flex-end; gap: .2rem;";

      const btnM = document.createElement("button");
      btnM.type = "button";
      btnM.className = "secondary";
      btnM.style.padding = ".2rem .5rem";
      btnM.textContent = "-";
      btnM.onclick = () => {
        if (dong.so_luong > 1) {
          dong.so_luong--;
          inpSl.value = dong.so_luong;
          tdThanhTien.textContent = Api.tien(dong.don_gia * dong.so_luong);
          tinhTien();
        }
      };

      const inpSl = document.createElement("input");
      inpSl.type = "number";
      inpSl.min = "1";
      inpSl.step = "1";
      inpSl.value = dong.so_luong;
      inpSl.style.cssText = "width: 60px; text-align: center; margin: 0; min-height: 2rem; padding: .2rem;";
      inpSl.onchange = () => {
        const moi = parseInt(inpSl.value, 10);
        if (moi > 0) {
          dong.so_luong = moi;
          tdThanhTien.textContent = Api.tien(dong.don_gia * dong.so_luong);
          tinhTien();
        } else {
          inpSl.value = dong.so_luong;
        }
      };

      const btnP = document.createElement("button");
      btnP.type = "button";
      btnP.className = "secondary";
      btnP.style.padding = ".2rem .5rem";
      btnP.textContent = "+";
      btnP.onclick = () => {
        dong.so_luong++;
        inpSl.value = dong.so_luong;
        tdThanhTien.textContent = Api.tien(dong.don_gia * dong.so_luong);
        tinhTien();
      };

      wrapSl.append(btnM, inpSl, btnP);
      tdSl.append(wrapSl);

      // Thành tiền
      const tdThanhTien = document.createElement("td");
      tdThanhTien.className = "so";
      tdThanhTien.innerHTML = `<strong>${Api.tien(dong.don_gia * dong.so_luong)}</strong>`;

      // Nút Xóa
      const tdXoa = document.createElement("td");
      tdXoa.style.textAlign = "center";
      const btnXoa = document.createElement("button");
      btnXoa.type = "button";
      btnXoa.className = "nguy-hiem";
      btnXoa.textContent = "×";
      btnXoa.title = "Xóa mặt hàng này khỏi đơn";
      btnXoa.onclick = () => {
        cacDongHang.splice(index, 1);
        capNhatBang();
      };
      tdXoa.append(btnXoa);

      tr.append(tdMa, tdTen, tdDvt, tdGia, tdSl, tdThanhTien, tdXoa);
      tbody.append(tr);
    });

    tinhTien();
  }

  // 6. Tính toán tiền và chiết khấu VIP 10%
  function tinhTien() {
    const tamTinh = cacDongHang.reduce((sum, d) => sum + d.don_gia * d.so_luong, 0);
    tamTinhEl.textContent = Api.tien(tamTinh);

    let giamVip = 0;
    const laVip = khachChon && khachChon.hang === "VIP";
    if (laVip && tamTinh > 0) {
      giamVip = Math.floor(tamTinh * 0.10);
      hangChietKhauVip.hidden = false;
      giamVipEl.textContent = "- " + Api.tien(giamVip);
    } else {
      hangChietKhauVip.hidden = true;
    }

    const phaiTra = Math.max(0, tamTinh - giamVip);
    phaiTraEl.textContent = Api.tien(phaiTra);
  }

  function xoaLoi() {
    loi.hidden = true;
    form.querySelectorAll(".loi-truong").forEach((e) => (e.textContent = ""));
    form.querySelectorAll("input.sai, select.sai").forEach((i) => i.classList.remove("sai"));
  }

  function hienLoi(e) {
    if (e.truong && form.querySelector(`[data-loi-truong="${e.truong}"]`)) {
      form.querySelector(`[data-loi-truong="${e.truong}"]`).textContent = e.thong_bao;
    } else {
      loi.textContent = e.thong_bao || "Có lỗi xảy ra khi lập đơn hàng";
      loi.hidden = false;
    }
  }

  // 7. Gửi lập đơn
  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    if(gui.disabled)return;
    xoaLoi();

    if (cacDongHang.length === 0) {
      loi.textContent = "Vui lòng chọn ít nhất một sản phẩm từ kho vào đơn.";
      loi.hidden = false;
      chonSpSelect.focus();
      return;
    }

    let ma_kh = null;
    let ten_kh = null;
    let sdt_kh = null;
    let dia_chi_kh = null;

    if (khachChon) {
      ma_kh = khachChon.ma_kh;
    } else if (tenKhMoiInput && tenKhMoiInput.value.trim() && sdtKhMoiInput && sdtKhMoiInput.value.trim()) {
      ten_kh = tenKhMoiInput.value.trim();
      sdt_kh = sdtKhMoiInput.value.trim();
      dia_chi_kh = diaChiKhMoiInput ? diaChiKhMoiInput.value.trim() : null;
      ma_kh = maKhTuDongEl ? maKhTuDongEl.value.trim() : null;
    } else if(!khoiThemKhachNhanh.hidden && (tenKhMoiInput.value.trim() || sdtKhMoiInput.value.trim())){
      loi.textContent="Điền đủ tên và số điện thoại, hoặc đóng phần thêm khách để bán cho khách lẻ.";
      loi.hidden=false;tenKhMoiInput.focus();return;
    }

    const payload = {
      ma_kh: ma_kh || null,
      ten_kh: ten_kh || null,
      sdt_kh: sdt_kh || null,
      dia_chi_kh: dia_chi_kh || null,
      dong: cacDongHang.map((d) => ({
        ma_sp: d.ma_sp,
        so_luong: d.so_luong
      }))
    };

    gui.disabled = true;
    gui.textContent = "Đang lập đơn…";
    form.setAttribute("aria-busy","true");
    try {
      const kq = await Api.post("/api/ban-hang/don-hang", payload);
      location.href = "/ban-hang/don-hang/" + encodeURIComponent(kq.ma_don);
    } catch (e) {
      hienLoi(e);
    } finally {
      gui.disabled = false;
      gui.textContent="Lập đơn & Giữ hàng";
      form.setAttribute("aria-busy","false");
    }
  });

  khoiTao();
}).catch(error=>Api.hienLoiPhien(error));
