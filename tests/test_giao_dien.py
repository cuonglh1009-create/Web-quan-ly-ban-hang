"""Hồi quy dữ liệu danh mục bị đặt nhầm trong thẻ title."""
import json
import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from kho_ban_hang.app import create_app
from kho_ban_hang.config.cau_hinh import CauHinh


class DuLieuGiaoDienTest(unittest.TestCase):
    def test_cac_trang_kho_dat_du_lieu_json_trong_noi_dung(self):
        with TemporaryDirectory() as tmp:
            app = create_app(CauHinh(str(Path(tmp) / "test.db"), khoa_bi_mat="template-regression-key"))
            result = app.test_cli_runner().invoke(args=[
                "seed", "--mat-khau-kho", "test-only-pass", "--mat-khau-ban-hang", "test-only-pass",
            ])
            self.assertEqual(result.exit_code, 0, result.output)
            client = app.test_client()
            csrf = client.get("/api/xac-thuc/phien").json["du_lieu"]["csrf_token"]
            login = client.post("/api/xac-thuc/dang-nhap", json={
                "ten_dang_nhap": "nv_kho", "mat_khau": "test-only-pass",
            }, headers={"X-CSRF-Token": csrf})
            self.assertEqual(login.status_code, 200)
            csrf = login.json["du_lieu"]["csrf_token"]
            from datetime import date
            receipt = client.post("/api/kho/phieu-nhap", json={
                "ma_ncc": "NCC01", "ngay_nhap": date.today().isoformat(),
                "dong": [{"ma_sp": "SP02", "ma_lo": "TEMPLATE-CHECK", "so_luong_nhap": 2, "gia_nhap": 100}],
            }, headers={"X-CSRF-Token": csrf})
            self.assertEqual(receipt.status_code, 201)
            code = receipt.json["du_lieu"]["ma_phieu"]
            for path in ["/kho", "/kho/lo-hang", "/kho/canh-bao", "/kho/san-pham", "/kho/phieu-nhap/" + code]:
                with self.subTest(path=path):
                    response = client.get(path)
                    self.assertEqual(response.status_code, 200)
                    html = response.get_data(as_text=True)
                    title = re.search(r"<title>(.*?)</title>", html, re.S).group(1)
                    self.assertNotIn("<script", title)
                    match = re.search(r'<script type="application/json" id="du-lieu-kho">(.*?)</script>', html, re.S)
                    self.assertIsNotNone(match)
                    self.assertGreater(match.start(), html.index("<body>"))
                    data = json.loads(match.group(1))
                    self.assertTrue(any(sp["ma_sp"] == "SP02" for sp in data["san_pham"]))


if __name__ == "__main__":
    unittest.main()
