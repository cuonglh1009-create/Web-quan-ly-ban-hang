Api.khoiTao({ batBuoc: "NV_BAN_HANG" }).then(async (phien) => {
  const form = document.getElementById("form-don"),
        tbody = document.getElementById("dong"),
        dongTrong = document.getElementById("dong-trong"),
        loi = document.getElementById("loi"),
        gui = document.getElementById("gui"),
        maDonEl = document.getElementById("ma-don-du-kien"),
        maKhTuDongEl = document.getElementById("ma-kh-tu-dong"),
        tenNhanVienEl = document.getElementById("ten-nhan-vien"),
        timKhachCuInput = document.getElementById("tim-khach-cu"),
        dsKhDatalist = document.getElementById("danh-sach-kh-goi-y"),
        thongTinKhEl = document.getElementById("thong-tin-kh-da-chon"),
        tenKhHienThi = document.getElementById("ten-kh-hien-thi"),
        maKhHienThi = document.getElementById("ma-kh-hien-thi"),
        sdtKhHienThi = document.getElementById("sdt-kh-hien-thi"),
        hangKhHienThi = document.getElementById("hang-kh-hien-thi"),
        nutBoChonKh = document.getElementById("nut-bo-chon-kh"),
        chonSpInput = document.getElementById("chon-sp-nhanh"),
        soLuongInput = document.getElementById("so-luong-nhanh"),
        nutThemSp = document.getElementById("nut-them-san-pham"),
        dsSpDatalist = document.getElementById("danh-sach-sp-goi-y"),
        tamTinhEl = document.getElementById("hien-thi-tam-tinh"),
        giamVipEl = document.getElementById("hien-thi-giam-vip"),
        hangChietKhauVip = document.getElementById("hang-chiet-khau-vip"),
        phaiTraEl = document.getElementById("hien-thi-phai-tra");

  if (phien && phien.nguoi_dung) {
    tenNhanVienEl.value = phien.nguoi_dung.ho_ten;
  }

  // Danh mục sản phẩm & khách hàng tải từ hệ thống
  let khoSanPhams = [];
  let danhSachKhach = [];
  let khachChon = null;
  const cacDongHang = []; // { ma_sp, ten_sp, don_vi_tinh, don_gia, so_luong, so_kha_dung }

  // 1. Tải thông tin khởi tạo: mã đơn, mã khách, gợi ý sản phẩm và khách hàng
  try {
    const [maData, spData, khData] = await Promise.all([
      Api.get("/api/ban-hang/ma-khoi-tao"),
      Api.get("/api/ban-hang/san-pham-goi-y"),
      Api.get("/api/ban-hang/khach-hang")
    ]);

    if (maData) {
      maDonEl.value = maData.ma_don_du_kien || "";
      maKhTuDongEl.value = maData.ma_kh_du_kien || "";
    }

    if (Array.isArray(spData)) {
      khoSanPhams = spData;
      dsSpDatalist.replaceChildren();
      for (const sp of spData) {
        const opt = document.createElement("option");
        opt.value = sp.ma_sp;
        opt.label = `${sp.ma_sp} - ${sp.ten_sp} (Đơn giá: ${Api.tien(sp.gia_niem_yet)} | Tồn kho: ${sp.so_kha_dung} ${sp.don_vi_tinh})`;
        dsSpDatalist.append(opt);
      }
    }

    if (Array.isArray(khData)) {
      danhSachKhach = khData;
      capNhatGoiYKhachHang(khData);
    }
  } catch (err) {
    console.error("Lỗi khởi tạo dữ liệu đơn mới:", err);
  }

  function capNhatGoiYKhachHang(danhSach) {
    dsKhDatalist.replaceChildren();
    for (const kh of danhSach) {
      const opt = document.createElement("option");
      opt.value = kh.ma_kh;
      const vipText = kh.hang === "VIP" ? " [VIP - Giảm 10%]" : "";
      opt.label = `${kh.ho_ten} (${kh.so_dien_thoai || "Không có SĐT"})${vipText}`;
      dsKhDatalist.append(opt);
    }
  }

  // 2. Xử lý chuyển đổi loại khách hàng (Cũ / Mới / Vãng lai)
  const radioLoaiKhach = form.querySelectorAll("input[name=loai_khach]");
  const khoiKhachCu = document.getElementById("khoi-khach-cu");
  const khoiKhachMoi = document.getElementById("khoi-khach-moi");

  radioLoaiKhach.forEach((r) => {
    r.addEventListener("change", () => {
      const val = form.loai_khach.value;
      if (val === "cu") {
        khoiKhachCu.hidden = false;
        khoiKhachMoi.hidden = true;
      } else if (val === "moi") {
        khoiKhachCu.hidden = true;
        khoiKhachMoi.hidden = false;
        boChonKhach();
      } else {
        khoiKhachCu.hidden = true;
        khoiKhachMoi.hidden = true;
        boChonKhach();
      }
      tinhTien();
    });
  });

  // Chọn khách hàng cũ từ gợi ý
  timKhachCuInput.addEventListener("input", () => {
    const val = timKhachCuInput.value.trim().toUpperCase();
    const found = danhSachKhach.find(
      (k) => k.ma_kh.toUpperCase() === val || k.so_dien_thoai === val || k.ho_ten.toUpperCase() === val
    );
    if (found) {
      chonKhach(found);
    }
  });

  function chonKhach(kh) {
    khachChon = kh;
    tenKhHienThi.textContent = kh.ho_ten;
    maKhHienThi.textContent = kh.ma_kh;
    sdtKhHienThi.textContent = kh.so_dien_thoai || "(Chưa có)";
    hangKhHienThi.textContent = kh.hang === "VIP" ? "VIP (Giảm 10%)" : "THƯỜNG";
    hangKhHienThi.className = "badge " + (kh.hang === "VIP" ? "success" : "");
    thongTinKhEl.hidden = false;
    timKhachCuInput.value = `${kh.ho_ten} (${kh.ma_kh})`;
    tinhTien();
  }

  function boChonKhach() {
    khachChon = null;
    thongTinKhEl.hidden = true;
    timKhachCuInput.value = "";
    tinhTien();
  }

  nutBoChonKh.onclick = boChonKhach;

  // 3. Thêm sản phẩm vào đơn từ gợi ý của kho (BỎ NÚT THÊM DÒNG THỦ CÔNG)
  nutThemSp.onclick = () => {
    xoaLoi();
    const ma = chonSpInput.value.trim().toUpperCase();
    const sl = parseInt(soLuongInput.value, 10);

    if (!ma) {
      chonSpInput.focus();
      return;
    }
    if (!sl || sl <= 0) {
      soLuongInput.focus();
      return;
    }

    const sp = khoSanPhams.find((p) => p.ma_sp.toUpperCase() === ma);
    if (!sp) {
      loi.textContent = `Không tìm thấy mã sản phẩm "${ma}" trong kho. Vui lòng chọn từ danh sách gợi ý.`;
      loi.hidden = false;
      return;
    }

    // Kiểm tra đã có trong danh sách chưa
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
        so_kha_dung: sp.so_kha_dung
      });
    }

    chonSpInput.value = "";
    soLuongInput.value = "1";
    chonSpInput.focus();
    capNhatBang();
  };

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
      tdMa.innerHTML = `<strong>${dong.ma_sp}</strong>`;

      // Tên SP
      const tdTen = document.createElement("td");
      tdTen.textContent = dong.ten_sp;

      // ĐVT
      const tdDvt = document.createElement("td");
      tdDvt.textContent = dong.don_vi_tinh;

      // Đơn giá
      const tdGia = document.createElement("td");
      tdGia.className = "so";
      tdGia.textContent = Api.tien(dong.don_gia);

      // Số lượng (ô input để người dùng chỉnh sửa)
      const tdSl = document.createElement("td");
      tdSl.className = "so";
      const inpSl = document.createElement("input");
      inpSl.type = "number";
      inpSl.min = "1";
      inpSl.step = "1";
      inpSl.value = dong.so_luong;
      inpSl.style.maxWidth = "90px";
      inpSl.style.textAlign = "right";
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
      tdSl.append(inpSl);

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
      btnXoa.title = "Xóa sản phẩm này";
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

  // 4. Tính toán tiền và chiết khấu VIP 10%
  function tinhTien() {
    const tamTinh = cacDongHang.reduce((sum, d) => sum + d.don_gia * d.so_luong, 0);
    tamTinhEl.textContent = Api.tien(tamTinh);

    let giamVip = 0;
    const laVip = khachChon && khachChon.hang === "VIP";
    if (laVip && tamTinh > 0) {
      giamVip = Math.floor(tamTinh * 0.10); // Giảm 10% cho khách VIP
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
    form.querySelectorAll("input.sai").forEach((i) => i.classList.remove("sai"));
  }

  function hienLoi(e) {
    if (e.truong && form.querySelector(`[data-loi-truong="${e.truong}"]`)) {
      form.querySelector(`[data-loi-truong="${e.truong}"]`).textContent = e.thong_bao;
    } else {
      loi.textContent = e.thong_bao || "Có lỗi xảy ra khi lập đơn";
      loi.hidden = false;
    }
  }

  // 5. Gửi lập đơn hàng
  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    xoaLoi();

    if (cacDongHang.length === 0) {
      loi.textContent = "Đơn hàng phải có ít nhất một sản phẩm từ kho.";
      loi.hidden = false;
      chonSpInput.focus();
      return;
    }

    const loaiKhach = form.loai_khach.value;
    let ma_kh = null;
    let ten_kh = null;
    let sdt_kh = null;
    let dia_chi_kh = null;

    if (loaiKhach === "cu") {
      ma_kh = khachChon ? khachChon.ma_kh : null;
    } else if (loaiKhach === "moi") {
      ten_kh = form.ten_kh.value.trim();
      sdt_kh = form.so_dien_thoai.value.trim();
      dia_chi_kh = form.dia_chi.value.trim();
      ma_kh = form.ma_kh_moi.value.trim() || null;

      if (!ten_kh) {
        hienLoi({ truong: "ten_kh", thong_bao: "Vui lòng nhập họ tên khách hàng" });
        return;
      }
      if (!sdt_kh) {
        hienLoi({ truong: "so_dien_thoai", thong_bao: "Vui lòng nhập số điện thoại" });
        return;
      }
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
    try {
      const kq = await Api.post("/api/ban-hang/don-hang", payload);
      location.href = "/ban-hang/don-hang/" + encodeURIComponent(kq.ma_don);
    } catch (e) {
      hienLoi(e);
    } finally {
      gui.disabled = false;
    }
  });
});
