Api.khoiTao({ batBuoc: "NV_BAN_HANG" }).then(() => {
  // 1. Quản lý chuyển Tab
  const tabButtons = document.querySelectorAll(".tab-btn"),
        tabPanels = document.querySelectorAll(".tab-panel");

  function chuyenTab(tabName) {
    tabButtons.forEach((btn) => {
      const active = btn.dataset.tab === tabName;
      btn.classList.toggle("active", active);
    });
    tabPanels.forEach((panel) => {
      panel.hidden = panel.id !== `panel-${tabName}`;
    });

    // Tải dữ liệu tương ứng theo tab
    if (tabName === "don-hang") taiDanhSachDon();
    else if (tabName === "khach-hang") taiDanhSachKhach();
    else if (tabName === "thong-ke") taiThongKe();
    else if (tabName === "tra-cuu-kho") taiTraCuuKho();
  }

  tabButtons.forEach((btn) => {
    btn.onclick = () => {
      const tab = btn.dataset.tab;
      chuyenTab(tab);
      // Cập nhật URL mà không reload trang
      const duongDan = tab === "don-hang" ? "/ban-hang/don-hang" : `/ban-hang/${tab}`;
      history.replaceState(null, "", duongDan);
    };
  });

  // Tự động nhận diện tab dựa trên đường dẫn URL
  const p = location.pathname;
  // Chờ các biến bảng và bộ lọc được khởi tạo xong trước khi tải tab.
  queueMicrotask(() => {
    if (p.includes("khach-hang")) chuyenTab("khach-hang");
    else if (p.includes("thong-ke")) chuyenTab("thong-ke");
    else if (p.includes("tra-cuu-kho")) chuyenTab("tra-cuu-kho");
    else chuyenTab("don-hang");
  });

  // ================= TAB 1: ĐƠN ĐÃ BÁN =================
  let locTrangThaiDon = "";
  const bangDonHang = document.getElementById("bang-don-hang"),
        formTimDon = document.getElementById("form-tim-don"),
        tuKhoaDonInput = document.getElementById("tu-khoa-don"),
        filterDonPills = document.querySelectorAll("#panel-don-hang .filter-pill");

  filterDonPills.forEach((pill) => {
    pill.onclick = () => {
      filterDonPills.forEach((p) => p.classList.remove("active"));
      pill.classList.add("active");
      locTrangThaiDon = pill.dataset.tt || "";
      taiDanhSachDon();
    };
  });

  formTimDon.onsubmit = (ev) => {
    ev.preventDefault();
    taiDanhSachDon();
  };

  async function taiDanhSachDon() {
    bangDonHang.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--muted); padding: 1.5rem;">Đang tải danh sách đơn hàng...</td></tr>`;
    try {
      const tk = tuKhoaDonInput.value.trim();
      let url = "/api/ban-hang/don-hang?";
      if (locTrangThaiDon) url += `trang_thai=${encodeURIComponent(locTrangThaiDon)}&`;
      if (tk) url += `tu_khoa=${encodeURIComponent(tk)}&`;

      const ds = await Api.get(url);
      bangDonHang.replaceChildren();

      if (!ds || ds.length === 0) {
        bangDonHang.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--muted); padding: 2rem;">Không tìm thấy đơn hàng nào.</td></tr>`;
        return;
      }

      for (const don of ds) {
        const tr = document.createElement("tr");

        // Mã đơn
        const tdMa = document.createElement("td");
        tdMa.innerHTML = `<a href="/ban-hang/don-hang/${encodeURIComponent(don.ma_don)}"><strong>${don.ma_don}</strong></a>`;

        // Ngày lập
        const tdNgay = document.createElement("td");
        tdNgay.textContent = don.ngay_lap;

        // Khách hàng
        const tdKh = document.createElement("td");
        if (don.ten_kh) {
          const vipBadge = don.hang_kh === "VIP" ? ` <span class="badge success" style="font-size: .75rem;">VIP</span>` : "";
          tdKh.innerHTML = `<strong>${don.ten_kh}</strong>${vipBadge}<br><small class="muted">${don.sdt_kh || don.ma_kh || ""}</small>`;
        } else {
          tdKh.innerHTML = `<span class="muted">Khách vãng lai</span>`;
        }

        // Nhân viên
        const tdNv = document.createElement("td");
        tdNv.textContent = don.ten_nv || don.ma_nv;

        // Tiền hàng
        const tdTienHang = document.createElement("td");
        tdTienHang.className = "so";
        tdTienHang.textContent = Api.tien(don.tong_tien_hang || 0);

        // Giảm giá
        const tdGiam = document.createElement("td");
        tdGiam.className = "so";
        const tongGiam = (don.giam_hang_khach || 0) + (don.giam_khuyen_mai || 0);
        tdGiam.textContent = tongGiam > 0 ? "- " + Api.tien(tongGiam) : "0 đ";

        // Thanh toán
        const tdThanhToan = document.createElement("td");
        tdThanhToan.className = "so";
        tdThanhToan.innerHTML = `<strong>${Api.tien(don.tong_thanh_toan || 0)}</strong>`;

        // Trạng thái badge
        const tdTrangThai = document.createElement("td");
        tdTrangThai.style.textAlign = "center";
        let badgeClass = "warning", nhanTt = "Chờ thanh toán";
        if (don.trang_thai === "DA_THANH_TOAN") {
          badgeClass = "success"; nhanTt = "Đã thanh toán";
        } else if (don.trang_thai === "DA_HUY") {
          badgeClass = "danger"; nhanTt = "Đã hủy";
        }
        tdTrangThai.innerHTML = `<span class="badge ${badgeClass}">${nhanTt}</span>`;

        // Thao tác
        const tdThaoTac = document.createElement("td");
        tdThaoTac.style.textAlign = "center";
        if (don.trang_thai === "DA_THANH_TOAN") {
          tdThaoTac.innerHTML = `
            <a href="/ban-hang/don-hang/${encodeURIComponent(don.ma_don)}/hoa-don" class="button secondary" style="padding: .25rem .6rem; font-size: .82rem;">Hóa đơn</a>
          `;
        } else {
          tdThaoTac.innerHTML = `
            <a href="/ban-hang/don-hang/${encodeURIComponent(don.ma_don)}" class="button secondary" style="padding: .25rem .6rem; font-size: .82rem;">Xem đơn</a>
          `;
        }

        tr.append(tdMa, tdNgay, tdKh, tdNv, tdTienHang, tdGiam, tdThanhToan, tdTrangThai, tdThaoTac);
        bangDonHang.append(tr);
      }
    } catch (err) {
      bangDonHang.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--loi); padding: 1.5rem;">Lỗi tải đơn hàng: ${err.thong_bao || err.message}</td></tr>`;
    }
  }

  // ================= TAB 2: QUẢN LÝ KHÁCH HÀNG =================
  const bangKhachHang = document.getElementById("bang-khach-hang"),
        formTraCuuKh = document.getElementById("form-tra-cuu-kh"),
        tuKhoaKhInput = document.getElementById("tu-khoa-kh"),
        nutXemTatCaKh = document.getElementById("nut-xem-tat-ca-kh"),
        nutMoThemKh = document.getElementById("nut-mo-them-kh"),
        khoiThemKh = document.getElementById("khoi-them-kh"),
        formThemKh = document.getElementById("form-them-kh-moi"),
        themMaKhInput = document.getElementById("them-ma-kh"),
        nutDongThemKh = document.getElementById("nut-dong-them-kh"),
        nutHuyThemKh = document.getElementById("nut-huy-them-kh"),
        loiThemKh = document.getElementById("loi-them-kh"),
        khoiLichSuKh = document.getElementById("khoi-lich-su-kh"),
        lsTenKh = document.getElementById("ls-ten-kh"),
        lsHangBadge = document.getElementById("ls-hang-badge"),
        bangLichSuKh = document.getElementById("bang-lich-su-kh"),
        nutDongLichSu = document.getElementById("nut-dong-lich-su");

  formTraCuuKh.onsubmit = (ev) => {
    ev.preventDefault();
    taiDanhSachKhach(tuKhoaKhInput.value.trim());
  };

  nutXemTatCaKh.onclick = () => {
    tuKhoaKhInput.value = "";
    taiDanhSachKhach();
  };

  nutMoThemKh.onclick = async () => {
    khoiThemKh.hidden = false;
    loiThemKh.hidden = true;
    formThemKh.reset();
    try {
      const maData = await Api.get("/api/ban-hang/ma-khoi-tao");
      if (maData && maData.ma_kh_du_kien) {
        themMaKhInput.value = maData.ma_kh_du_kien;
      }
    } catch (_) {}
    formThemKh.ho_ten.focus();
  };

  nutDongThemKh.onclick = () => { khoiThemKh.hidden = true; };
  nutHuyThemKh.onclick = () => { khoiThemKh.hidden = true; };
  nutDongLichSu.onclick = () => { khoiLichSuKh.hidden = true; };

  formThemKh.onsubmit = async (ev) => {
    ev.preventDefault();
    loiThemKh.hidden = true;
    const ho_ten = formThemKh.ho_ten.value.trim();
    const so_dien_thoai = formThemKh.so_dien_thoai.value.trim();
    const dia_chi = formThemKh.dia_chi.value.trim();
    const ma_kh = themMaKhInput.value.trim();

    if (!ho_ten) {
      loiThemKh.textContent = "Vui lòng nhập họ tên khách hàng";
      loiThemKh.hidden = false;
      return;
    }
    if (!so_dien_thoai) {
      loiThemKh.textContent = "Vui lòng nhập số điện thoại";
      loiThemKh.hidden = false;
      return;
    }

    try {
      await Api.post("/api/ban-hang/khach-hang", { ma_kh, ho_ten, so_dien_thoai, dia_chi });
      khoiThemKh.hidden = true;
      formThemKh.reset();
      taiDanhSachKhach();
    } catch (err) {
      loiThemKh.textContent = err.thong_bao || "Lỗi lưu khách hàng";
      loiThemKh.hidden = false;
    }
  };

  async function taiDanhSachKhach(tuKhoa = "") {
    bangKhachHang.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--muted); padding: 1.5rem;">Đang tải dữ liệu khách hàng...</td></tr>`;
    try {
      const url = tuKhoa ? `/api/ban-hang/khach-hang?tu_khoa=${encodeURIComponent(tuKhoa)}` : `/api/ban-hang/khach-hang`;
      const ds = await Api.get(url);
      bangKhachHang.replaceChildren();

      if (!ds || ds.length === 0) {
        bangKhachHang.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--muted); padding: 2rem;">Không tìm thấy khách hàng nào phù hợp với từ khóa.</td></tr>`;
        return;
      }

      for (const kh of ds) {
        const tr = document.createElement("tr");

        // Mã KH
        const tdMa = document.createElement("td");
        tdMa.innerHTML = `<strong>${kh.ma_kh}</strong>`;

        // Họ tên
        const tdTen = document.createElement("td");
        tdTen.innerHTML = `<strong>${kh.ho_ten}</strong>`;

        // SĐT
        const tdSdt = document.createElement("td");
        tdSdt.textContent = kh.so_dien_thoai || "(Chưa có)";

        // Địa chỉ
        const tdDiaChi = document.createElement("td");
        tdDiaChi.textContent = kh.dia_chi || "-";

        // Điểm tích lũy
        const tdDiem = document.createElement("td");
        tdDiem.className = "so";
        tdDiem.textContent = kh.diem_tich_luy || 0;

        // Hạng (VIP hay Thường)
        const tdHang = document.createElement("td");
        tdHang.style.textAlign = "center";
        const laVip = kh.hang === "VIP";
        tdHang.innerHTML = `<span class="badge ${laVip ? "success" : ""}">${laVip ? "VIP ⭐ (Giảm 10%)" : "THƯỜNG"}</span>`;

        // Tổng chi tiêu
        const tdChiTieu = document.createElement("td");
        tdChiTieu.className = "so";
        tdChiTieu.innerHTML = `<strong>${Api.tien(kh.tong_chi_tieu || 0)}</strong>`;

        // Số đơn
        const tdSoDon = document.createElement("td");
        tdSoDon.className = "so";
        tdSoDon.textContent = kh.so_don_thanh_cong || 0;

        // Lịch sử mua hàng
        const tdThaoTac = document.createElement("td");
        tdThaoTac.style.textAlign = "center";
        const btnLs = document.createElement("button");
        btnLs.type = "button";
        btnLs.className = "secondary";
        btnLs.style.padding = ".25rem .6rem";
        btnLs.style.fontSize = ".82rem";
        btnLs.textContent = "Xem đơn";
        btnLs.onclick = () => xemLichSuKhach(kh);
        tdThaoTac.append(btnLs);

        tr.append(tdMa, tdTen, tdSdt, tdDiaChi, tdDiem, tdHang, tdChiTieu, tdSoDon, tdThaoTac);
        bangKhachHang.append(tr);
      }
    } catch (err) {
      bangKhachHang.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--loi); padding: 1.5rem;">Lỗi tải khách hàng: ${err.thong_bao || err.message}</td></tr>`;
    }
  }

  async function xemLichSuKhach(kh) {
    lsTenKh.textContent = `${kh.ho_ten} (${kh.ma_kh})`;
    lsHangBadge.textContent = kh.hang === "VIP" ? "VIP" : "THƯỜNG";
    lsHangBadge.className = "badge " + (kh.hang === "VIP" ? "success" : "");
    khoiLichSuKh.hidden = false;
    khoiLichSuKh.scrollIntoView({ behavior: "smooth" });

    bangLichSuKh.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--muted); padding: 1rem;">Đang tải lịch sử đơn hàng...</td></tr>`;
    try {
      const ds = await Api.get(`/api/ban-hang/khach-hang/${encodeURIComponent(kh.ma_kh)}/don-hang`);
      bangLichSuKh.replaceChildren();

      if (!ds || ds.length === 0) {
        bangLichSuKh.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--muted); padding: 1rem;">Khách hàng chưa có đơn mua nào.</td></tr>`;
        return;
      }

      for (const d of ds) {
        const tr = document.createElement("tr");
        const tdMa = document.createElement("td");
        tdMa.innerHTML = `<strong>${d.ma_don}</strong>`;

        const tdNgay = document.createElement("td");
        tdNgay.textContent = d.ngay_lap;

        const tdNv = document.createElement("td");
        tdNv.textContent = d.ten_nv || "-";

        const tdTien = document.createElement("td");
        tdTien.className = "so";
        tdTien.innerHTML = `<strong>${Api.tien(d.tong_thanh_toan || 0)}</strong>`;

        const tdTt = document.createElement("td");
        let badgeClass = "warning", nhan = "Chờ thanh toán";
        if (d.trang_thai === "DA_THANH_TOAN") { badgeClass = "success"; nhan = "Đã thanh toán"; }
        else if (d.trang_thai === "DA_HUY") { badgeClass = "danger"; nhan = "Đã hủy"; }
        tdTt.innerHTML = `<span class="badge ${badgeClass}">${nhan}</span>`;

        const tdXem = document.createElement("td");
        tdXem.style.textAlign = "center";
        tdXem.innerHTML = `<a href="/ban-hang/don-hang/${encodeURIComponent(d.ma_don)}" class="button secondary" style="padding: .2rem .5rem; font-size: .8rem;">Chi tiết</a>`;

        tr.append(tdMa, tdNgay, tdNv, tdTien, tdTt, tdXem);
        bangLichSuKh.append(tr);
      }
    } catch (err) {
      bangLichSuKh.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--loi); padding: 1rem;">Lỗi: ${err.thong_bao || err.message}</td></tr>`;
    }
  }

  // ================= TAB 3: THỐNG KÊ DOANH THU & SẢN PHẨM =================
  let kieuThongKeDoanhThu = "ngay";
  const bangDoanhThu = document.getElementById("bang-thong-ke-doanh-thu"),
        bangSanpham = document.getElementById("bang-thong-ke-san-pham"),
        cotThoiGian = document.getElementById("cot-thoi-gian"),
        tongDoanhThuEl = document.getElementById("tk-tong-doanh-thu"),
        tongDonEl = document.getElementById("tk-tong-don"),
        tongGiamEl = document.getElementById("tk-tong-giam"),
        pillsDoanhThu = document.querySelectorAll("#panel-thong-ke .filter-pill");

  pillsDoanhThu.forEach((pill) => {
    pill.onclick = () => {
      pillsDoanhThu.forEach((p) => p.classList.remove("active"));
      pill.classList.add("active");
      kieuThongKeDoanhThu = pill.dataset.kieu || "ngay";
      taiThongKeDoanhThu();
    };
  });

  async function taiThongKe() {
    await Promise.all([taiThongKeDoanhThu(), taiThongKeSanPham()]);
  }

  async function taiThongKeDoanhThu() {
    cotThoiGian.textContent = kieuThongKeDoanhThu === "nam" ? "Năm" : (kieuThongKeDoanhThu === "thang" ? "Tháng (YYYY-MM)" : "Ngày (YYYY-MM-DD)");
    bangDoanhThu.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--muted); padding: 1.5rem;">Đang tải dữ liệu...</td></tr>`;

    try {
      const ds = await Api.get(`/api/ban-hang/thong-ke/doanh-thu?kieu=${kieuThongKeDoanhThu}`);
      bangDoanhThu.replaceChildren();

      if (!ds || ds.length === 0) {
        bangDoanhThu.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--muted); padding: 1.5rem;">Chưa có dữ liệu doanh thu nào từ đơn đã thanh toán.</td></tr>`;
        tongDoanhThuEl.textContent = "0 đ";
        tongDonEl.textContent = "0";
        tongGiamEl.textContent = "0 đ";
        return;
      }

      let tongThu = 0, tongDon = 0, tongGiam = 0;
      for (const row of ds) {
        tongThu += row.doanh_thu || 0;
        tongDon += row.so_don || 0;
        tongGiam += row.tong_giam || 0;

        const tr = document.createElement("tr");

        const tdTime = document.createElement("td");
        tdTime.innerHTML = `<strong>${row.thoi_gian}</strong>`;

        const tdSoDon = document.createElement("td");
        tdSoDon.className = "so";
        tdSoDon.textContent = row.so_don;

        const tdTienHang = document.createElement("td");
        tdTienHang.className = "so";
        tdTienHang.textContent = Api.tien(row.tong_tien_hang || 0);

        const tdGiam = document.createElement("td");
        tdGiam.className = "so";
        tdGiam.textContent = Api.tien(row.tong_giam || 0);

        const tdDoanhThu = document.createElement("td");
        tdDoanhThu.className = "so";
        tdDoanhThu.innerHTML = `<strong style="color: var(--accent);">${Api.tien(row.doanh_thu || 0)}</strong>`;

        tr.append(tdTime, tdSoDon, tdTienHang, tdGiam, tdDoanhThu);
        bangDoanhThu.append(tr);
      }

      tongDoanhThuEl.textContent = Api.tien(tongThu);
      tongDonEl.textContent = tongDon;
      tongGiamEl.textContent = Api.tien(tongGiam);
    } catch (err) {
      bangDoanhThu.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--loi); padding: 1.5rem;">Lỗi: ${err.thong_bao || err.message}</td></tr>`;
    }
  }

  async function taiThongKeSanPham() {
    bangSanpham.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--muted); padding: 1.5rem;">Đang tải thống kê sản phẩm...</td></tr>`;
    try {
      const ds = await Api.get("/api/ban-hang/thong-ke/san-pham");
      bangSanpham.replaceChildren();

      if (!ds || ds.length === 0) {
        bangSanpham.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--muted); padding: 1.5rem;">Chưa có sản phẩm nào được bán.</td></tr>`;
        return;
      }

      ds.forEach((sp, idx) => {
        const tr = document.createElement("tr");

        const tdHang = document.createElement("td");
        tdHang.style.textAlign = "center";
        const topClass = idx === 0 ? "success" : (idx <= 2 ? "warning" : "");
        tdHang.innerHTML = `<span class="badge ${topClass}" style="font-weight: 700;">#${idx + 1}</span>`;

        const tdMa = document.createElement("td");
        tdMa.innerHTML = `<strong>${sp.ma_sp}</strong>`;

        const tdTen = document.createElement("td");
        tdTen.innerHTML = `<strong>${sp.ten_sp}</strong>`;

        const tdDvt = document.createElement("td");
        tdDvt.textContent = sp.don_vi_tinh;

        const tdSl = document.createElement("td");
        tdSl.className = "so";
        tdSl.innerHTML = `<strong style="font-size: 1.05rem;">${sp.tong_so_luong}</strong> ${sp.don_vi_tinh}`;

        const tdDt = document.createElement("td");
        tdDt.className = "so";
        tdDt.innerHTML = `<strong style="color: var(--accent);">${Api.tien(sp.tong_doanh_thu || 0)}</strong>`;

        tr.append(tdHang, tdMa, tdTen, tdDvt, tdSl, tdDt);
        bangSanpham.append(tr);
      });
    } catch (err) {
      bangSanpham.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--loi); padding: 1.5rem;">Lỗi: ${err.thong_bao || err.message}</td></tr>`;
    }
  }

  // ================= TAB 4: TRA CỨU HÀNG TRONG KHO =================
  const bangTraCuuKho = document.getElementById("bang-tra-cuu-kho"),
        formTimKho = document.getElementById("form-tim-kho"),
        tuKhoaKhoInput = document.getElementById("tu-khoa-kho"),
        nutLamMoiKhoTab = document.getElementById("nut-lam-moi-kho-tab"),
        thoiGianKhoSync = document.getElementById("thoi-gian-kho-sync");

  if (nutLamMoiKhoTab) {
    nutLamMoiKhoTab.onclick = () => taiTraCuuKho(tuKhoaKhoInput.value.trim());
  }

  formTimKho.onsubmit = (ev) => {
    ev.preventDefault();
    taiTraCuuKho(tuKhoaKhoInput.value.trim());
  };

  async function taiTraCuuKho(tuKhoa = "") {
    bangTraCuuKho.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--muted); padding: 1.5rem;">Đang tải danh sách hàng trong kho...</td></tr>`;
    if (thoiGianKhoSync) thoiGianKhoSync.textContent = "Đang đồng bộ...";
    try {
      const url = tuKhoa ? `/api/ban-hang/tra-cuu-kho?tu_khoa=${encodeURIComponent(tuKhoa)}` : `/api/ban-hang/tra-cuu-kho`;
      const ds = await Api.get(url);
      bangTraCuuKho.replaceChildren();

      const now = new Date();
      const gio = String(now.getHours()).padStart(2, "0") + ":" +
                  String(now.getMinutes()).padStart(2, "0") + ":" +
                  String(now.getSeconds()).padStart(2, "0");
      if (thoiGianKhoSync) thoiGianKhoSync.textContent = `Đồng bộ lúc ${gio}`;

      if (!ds || ds.length === 0) {
        bangTraCuuKho.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--muted); padding: 2rem;">Không tìm thấy mặt hàng nào trong kho.</td></tr>`;
        return;
      }

      for (const sp of ds) {
        const tr = document.createElement("tr");

        const tdMa = document.createElement("td");
        tdMa.innerHTML = `<strong>${sp.ma_sp}</strong>`;

        const tdTen = document.createElement("td");
        tdTen.innerHTML = `<strong>${sp.ten_sp}</strong>`;

        const tdDm = document.createElement("td");
        tdDm.textContent = sp.danh_muc || "-";

        const tdDvt = document.createElement("td");
        tdDvt.textContent = sp.don_vi_tinh;

        const tdGia = document.createElement("td");
        tdGia.className = "so";
        tdGia.innerHTML = `<strong>${Api.tien(sp.gia_niem_yet)}</strong>`;

        const tdTon = document.createElement("td");
        tdTon.className = "so";
        tdTon.innerHTML = `<strong style="font-size: 1.05rem; color: ${sp.so_kha_dung > 0 ? "var(--accent)" : "var(--loi)"};">${sp.so_kha_dung}</strong>`;

        const tdNcc = document.createElement("td");
        tdNcc.textContent = sp.nha_cung_cap || "Nhà cung cấp An Phú";

        const tdTt = document.createElement("td");
        tdTt.style.textAlign = "center";
        if (sp.so_kha_dung <= 0) {
          tdTt.innerHTML = `<span class="badge danger">Hết hàng</span>`;
        } else if (sp.so_kha_dung <= 5) {
          tdTt.innerHTML = `<span class="badge warning">Sắp hết hàng</span>`;
        } else {
          tdTt.innerHTML = `<span class="badge success">Còn hàng</span>`;
        }

        const tdThaoTac = document.createElement("td");
        tdThaoTac.style.textAlign = "center";
        const btnLapDon = document.createElement("button");
        btnLapDon.type = "button";
        btnLapDon.className = "secondary";
        btnLapDon.style.padding = ".25rem .6rem";
        btnLapDon.style.fontSize = ".82rem";
        btnLapDon.textContent = "+ Chọn mua";
        btnLapDon.onclick = () => {
          sessionStorage.setItem("chon_san_pham_ma", sp.ma_sp);
          location.href = "/ban-hang/don-hang/moi";
        };
        tdThaoTac.append(btnLapDon);

        tr.append(tdMa, tdTen, tdDm, tdDvt, tdGia, tdTon, tdNcc, tdTt, tdThaoTac);
        bangTraCuuKho.append(tr);
      }
    } catch (err) {
      bangTraCuuKho.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--loi); padding: 1.5rem;">Lỗi tải kho: ${err.thong_bao || err.message}</td></tr>`;
    }
  }
});
