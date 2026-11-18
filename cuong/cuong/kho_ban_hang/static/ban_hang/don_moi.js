Api.khoiTao({ batBuoc: "NV_BAN_HANG" }).then(() => {
  const form = document.getElementById("form-don"), tbody = document.getElementById("dong"),
        loi = document.getElementById("loi"), gui = document.getElementById("gui");

  function themDong(ma = "", sl = "1") {
    const tr = document.createElement("tr");
    for (const [ten, gia, kieu] of [["ma_sp", ma, "text"], ["so_luong", sl, "number"]]) {
      const td = document.createElement("td"), inp = document.createElement("input");
      inp.name = ten; inp.value = gia; inp.type = kieu; if (kieu === "number") { inp.min = "1"; inp.step = "1"; }
      const e = document.createElement("span"); e.className = "loi-truong"; e.dataset.ten = ten;
      td.append(inp, e); tr.append(td);
    }
    const td = document.createElement("td"), xoa = document.createElement("button");
    xoa.type = "button"; xoa.textContent = "Xóa";
    xoa.onclick = () => { if (tbody.rows.length > 1) tr.remove(); };
    td.append(xoa); tr.append(td); tbody.append(tr);
  }

  function xoaLoi() {
    loi.hidden = true;
    form.querySelectorAll(".loi-truong").forEach((e) => (e.textContent = ""));
    form.querySelectorAll("input.sai").forEach((i) => i.classList.remove("sai"));
  }

  function hienLoi(e) {
    const m = /^dong\[(\d+)\]\.(ma_sp|so_luong)$/.exec(e.truong || "");
    if (m && tbody.rows[+m[1]]) {                                   // lỗi gắn đúng dòng
      const o = tbody.rows[+m[1]].querySelector(`[name=${m[2]}]`);
      o.classList.add("sai"); o.nextElementSibling.textContent = e.thong_bao; o.focus();
    } else if (e.truong === "ma_kh") {
      form.querySelector("[data-loi-truong=ma_kh]").textContent = e.thong_bao;
    } else { loi.textContent = e.thong_bao; loi.hidden = false; }   // lỗi chung, vd hết hàng
  }

  document.getElementById("them-dong").onclick = () => themDong();
  themDong();

  form.addEventListener("submit", async (ev) => {
    ev.preventDefault(); xoaLoi();
    const dong = [...tbody.rows].map((tr) => ({
      ma_sp: tr.querySelector("[name=ma_sp]").value.trim(),
      so_luong: Number(tr.querySelector("[name=so_luong]").value) }));
    gui.disabled = true;                                           // chống bấm đúp
    try {
      const kq = await Api.post("/api/ban-hang/don-hang", { ma_kh: form.ma_kh.value.trim() || null, dong });
      location.href = "/ban-hang/don-hang/" + encodeURIComponent(kq.ma_don);
    } catch (e) { hienLoi(e); }                                    // form giữ nguyên dữ liệu
    finally { gui.disabled = false; }
  });
});
