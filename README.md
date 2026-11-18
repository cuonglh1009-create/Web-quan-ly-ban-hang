# Quản lý kho và bán hàng

Ứng dụng Flask dùng SQLite chung cho hai phân hệ. Khi lập đơn, Bán hàng giữ hàng theo lô trong Kho. Thanh toán xác nhận xuất kho và tạo hóa đơn. Hủy đơn chờ thanh toán sẽ trả hàng đã giữ về tồn khả dụng.

## Chạy trên máy tính

Cần Python 3.11 trở lên. Mở PowerShell tại thư mục chứa `requirements.txt` và chạy:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:KBH_KHOA_BI_MAT = [Guid]::NewGuid().ToString("N")
.\.venv\Scripts\python.exe -m flask --app kho_ban_hang.app seed
.\.venv\Scripts\python.exe -m flask --app kho_ban_hang.app run
```

Lệnh `seed` tạo tệp `kho_ban_hang.db` và yêu cầu đặt mật khẩu (ít nhất 8 ký tự) cho từng tài khoản mẫu. Dùng `tao-schema` thay cho `seed` nếu chỉ cần tạo các bảng.

Mở [ứng dụng trên máy tính](http://127.0.0.1:5000/). Đăng nhập bằng `nv_kho` để lập phiếu nhập, xem lô hàng và cảnh báo. Dùng `nv_ban_hang` để lập đơn, thanh toán và tra cứu hóa đơn. Có thể dùng mã `SP03` để thử bán áo thun từ tồn kho mẫu.

Bản gộp khởi tạo cơ sở dữ liệu riêng. Tệp demo của phần Kho vẫn có trong commit ban đầu của Văn Tuyến (`89381e1`).
