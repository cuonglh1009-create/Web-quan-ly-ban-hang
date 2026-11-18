export async function goiApi(url, { method = "GET", body, signal } = {}) {
  const headers = { Accept: "application/json" };
  if (method === "POST") {
    headers["Content-Type"] = "application/json";
    headers["X-CSRF-Token"] = document.querySelector('meta[name="csrf-token"]').content;
  }
  const response = await fetch(url, {
    method, headers, signal, body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (response.status === 401) {
    location.assign("/dang-nhap");
    throw new Error("Phiên đăng nhập đã hết hạn.");
  }
  const ketQua = await response.json().catch(() => null);
  if (!response.ok || !ketQua || !("du_lieu" in ketQua)) {
    const loi = new Error(ketQua?.loi?.thong_bao || "Không xử lý được yêu cầu. Vui lòng thử lại.");
    loi.truong = ketQua?.loi?.truong;
    throw loi;
  }
  return ketQua.du_lieu;
}
