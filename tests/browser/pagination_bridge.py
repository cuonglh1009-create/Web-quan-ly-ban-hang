import base64
import json
import sys
from pathlib import Path

from kho_ban_hang.app import create_app
from kho_ban_hang.config.cau_hinh import CauHinh

app = create_app(CauHinh(duong_dan_csdl=sys.argv[1], khoa_bi_mat="temporary-browser-test-secret"))
result = app.test_cli_runner().invoke(args=[
    "seed", "--mat-khau-kho", "test-only-pass", "--mat-khau-ban-hang", "test-only-pass",
])
assert result.exit_code == 0, (result.output, repr(result.exception))

from datetime import date
from kho_ban_hang.repositories.giao_dich import ket_noi
with ket_noi(sys.argv[1]) as db:
    today=date.today().isoformat()
    db.executemany("INSERT INTO lo_hang VALUES (?, 'SP02',?,NULL,NULL,2,100)",[(f"PAGE-LOT-{i:03}",today) for i in range(33)])
    db.executemany("INSERT INTO phieu_nhap VALUES (?,?,'NV001','NCC01','NHAP')",[(f"PAGE-PN-{i:03}",today) for i in range(31)])
    db.executemany("INSERT INTO don_hang(ma_don,ngay_lap,trang_thai,ma_nv) VALUES (?,?,'CHO_THANH_TOAN','NV002')",[(f"PAGE-DH-{i:03}",today) for i in range(31)])
    db.executemany("INSERT INTO khach_hang(ma_kh,ho_ten,so_dien_thoai,dia_chi,diem_tich_luy,hang) VALUES (?,?,?,'Hà Nội',0,'THUONG')",[(f"PAGE-KH-{i:03}",f"Khách thử {i}","0900000000") for i in range(43)])

client = app.test_client(use_cookies=False)
for line in sys.stdin:
    req = json.loads(line)
    response = client.open(req["path"], method=req["method"], headers=req["headers"],
                           data=base64.b64decode(req["body"]))
    print(json.dumps({"id": req["id"], "status": response.status_code,
                     "headers": dict(response.headers),
                     "body": base64.b64encode(response.data).decode()}), flush=True)
