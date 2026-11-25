import unittest
from contextlib import closing
from dataclasses import FrozenInstanceError
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from kho_ban_hang.app import create_app
from kho_ban_hang.config.cau_hinh import CauHinh
from kho_ban_hang.domain.errors import DuLieuKhongHopLeError
from kho_ban_hang.domain.enums_kho import LoaiSanPham
from kho_ban_hang.domain.san_pham_factory import (
    SanPhamFactory, HangDienTuFactory, HangThucPhamFactory,
)
from kho_ban_hang.repositories.kho.danh_muc_repository import DanhMucRepository
from kho_ban_hang.repositories.kho.san_pham_repository import SanPhamRepository
from kho_ban_hang.repositories.giao_dich import ket_noi


class KiemThuNangCapOOP(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.database = str(Path(tmp.name) / "test.db")
        self.app = create_app(CauHinh(duong_dan_csdl=self.database, khoa_bi_mat="unit-test-key-only"))
        result = self.app.test_cli_runner().invoke(args=[
            "seed", "--mat-khau-kho", "test-only-pass", "--mat-khau-ban-hang", "test-only-pass",
        ])
        self.assertEqual(result.exit_code, 0, result.output)
        self.client = self.app.test_client()

    def dang_nhap(self, mat_khau):
        csrf = self.client.get("/api/xac-thuc/phien").json["du_lieu"]["csrf_token"]
        return self.client.post("/api/xac-thuc/dang-nhap", json={
            "ten_dang_nhap": "nv_kho", "mat_khau": mat_khau,
        }, headers={"X-CSRF-Token": csrf})

    def test_mat_khau_bat_buoc_va_xac_minh_bam(self):
        self.assertEqual(self.dang_nhap("").status_code, 400)
        self.assertEqual(self.dang_nhap("sai-mat-khau").status_code, 401)
        self.assertEqual(self.client.get("/api/kho/lo-hang").status_code, 401)
        response = self.dang_nhap("test-only-pass")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["du_lieu"]["nguoi_dung"]["vai_tro"], "NV_KHO")

    def test_factory_va_da_hinh_san_pham(self):
        with closing(ket_noi(self.database)) as conn:
            repo = SanPhamRepository(conn, DanhMucRepository(conn))
            thuc_pham = repo.tim_theo_ma("SP01")
            dien_tu = repo.tim_theo_ma("SP02")
            self.assertTrue(thuc_pham.can_ngay_lo)
            self.assertFalse(dien_tu.can_ngay_lo)
            self.assertIsInstance(HangDienTuFactory(), SanPhamFactory)
            self.assertIsInstance(HangThucPhamFactory(), SanPhamFactory)
            self.assertEqual(dien_tu.loai, LoaiSanPham.DIEN_TU)
            with self.assertRaises(FrozenInstanceError):
                dien_tu.gia_niem_yet = -1
            with self.assertRaises(DuLieuKhongHopLeError):
                dien_tu.cap_nhat_gia(-1)
            dien_tu.cap_nhat_gia(123456)
            self.assertEqual(dien_tu.gia_niem_yet, 123456)

    def test_phieu_mien_chi_cho_chuyen_trang_thai_qua_phuong_thuc(self):
        from kho_ban_hang.repositories.ban_hang.nhan_vien_repository import NhanVienRepository
        from kho_ban_hang.services.kho.dang_ky import dang_ky_kho
        from kho_ban_hang.contracts.kho_dto import DongNhapDTO, PhieuNhapDTO
        with closing(ket_noi(self.database)) as conn:
            nv_repo = NhanVienRepository(conn)
            parts = dang_ky_kho(conn, CauHinh(self.database), nv_repo.tim_theo_ma)
            phieu = parts.nhap_kho.lap_phieu(
                PhieuNhapDTO("NCC01", date.today(), [DongNhapDTO("SP02", "LO-TEST", 2, 100)]),
                nv_repo.tim_theo_ma("NV001"),
            )
            with self.assertRaises(AttributeError):
                phieu.trang_thai = "INVALID"
            self.assertIsInstance(phieu.chi_tiet, tuple)
            with self.assertRaises(FrozenInstanceError):
                phieu.chi_tiet[0].lo_hang.so_luong_con_lai = -1
            completed = parts.nhap_kho.xac_nhan_phieu(phieu.ma_phieu, date.today())
            repeated = parts.nhap_kho.xac_nhan_phieu(phieu.ma_phieu, date.today())
            self.assertEqual(completed.trang_thai, repeated.trang_thai)
            self.assertEqual(parts.kho.lay_so_luong_kha_dung("SP02"), 5)

    def test_rate_limit_sau_cac_lan_sai_mat_khau(self):
        for _ in range(5):
            self.assertEqual(self.dang_nhap("wrong-password").status_code, 401)
        self.assertEqual(self.dang_nhap("test-only-pass").status_code, 429)

    def test_chuc_nang_moi_nhan_vien_ban_hang(self):
        # 1. Đăng nhập nhân viên bán hàng
        csrf = self.client.get("/api/xac-thuc/phien").json["du_lieu"]["csrf_token"]
        res_dn = self.client.post("/api/xac-thuc/dang-nhap", json={
            "ten_dang_nhap": "nv_ban_hang", "mat_khau": "test-only-pass",
        }, headers={"X-CSRF-Token": csrf})
        self.assertEqual(res_dn.status_code, 200)
        csrf = res_dn.json["du_lieu"]["csrf_token"]

        # 2. Gợi ý sản phẩm và tra cứu hàng trong kho
        res_sp = self.client.get("/api/ban-hang/san-pham-goi-y")
        self.assertEqual(res_sp.status_code, 200)
        cac_sp = res_sp.json["du_lieu"]
        self.assertTrue(len(cac_sp) >= 3)
        self.assertTrue(any(sp["ma_sp"] == "SP01" and sp["so_kha_dung"] > 0 for sp in cac_sp))

        res_kho = self.client.get("/api/ban-hang/tra-cuu-kho")
        self.assertEqual(res_kho.status_code, 200)
        self.assertTrue(any(item["nha_cung_cap"] for item in res_kho.json["du_lieu"]))

        # 3. Mã khởi tạo tự động
        res_ma = self.client.get("/api/ban-hang/ma-khoi-tao")
        self.assertEqual(res_ma.status_code, 200)
        self.assertTrue(res_ma.json["du_lieu"]["ma_don_du_kien"].startswith("DH"))
        self.assertTrue(res_ma.json["du_lieu"]["ma_kh_du_kien"].startswith("KH"))

        # 4. Lập đơn với khách VIP (KH003) -> Giảm 10% chiết khấu VIP
        # SP02: đơn giá 230.000đ, số lượng 2 -> tạm tính 460.000đ -> giảm 10% = 46.000đ -> phải trả 414.000đ
        res_don_vip = self.client.post("/api/ban-hang/don-hang", json={
            "ma_kh": "KH003",
            "dong": [{"ma_sp": "SP02", "so_luong": 2}]
        }, headers={"X-CSRF-Token": csrf})
        self.assertEqual(res_don_vip.status_code, 201)
        don_vip = res_don_vip.json["du_lieu"]
        self.assertEqual(don_vip["tam_tinh"], 460_000)
        self.assertEqual(don_vip["giam_hang_khach"], 46_000)   # 10% cho khách VIP
        self.assertEqual(don_vip["so_phai_tra"], 414_000)

        # 5. Lập đơn với khách hàng mới tự động điền mã và thông tin
        res_don_moi = self.client.post("/api/ban-hang/don-hang", json={
            "ten_kh": "Hoàng Minh Tuấn",
            "sdt_kh": "0987654321",
            "dia_chi_kh": "Hà Nội",
            "dong": [{"ma_sp": "SP01", "so_luong": 1}]
        }, headers={"X-CSRF-Token": csrf})
        self.assertEqual(res_don_moi.status_code, 201)
        don_kh_moi = res_don_moi.json["du_lieu"]

        # 6. Thanh toán đơn hàng
        res_tt = self.client.post(f"/api/ban-hang/don-hang/{don_vip['ma_don']}/thanh-toan", json={
            "phuong_thuc": "TIEN_MAT",
            "thong_tin": {"tien_khach_dua": 500_000}
        }, headers={"X-CSRF-Token": csrf})
        self.assertEqual(res_tt.status_code, 200)

        # 7. Danh sách đơn hàng đã bán
        res_ds_don = self.client.get("/api/ban-hang/don-hang")
        self.assertEqual(res_ds_don.status_code, 200)
        self.assertTrue(len(res_ds_don.json["du_lieu"]) >= 2)

        # 8. Tra cứu khách hàng theo mã đơn, tên, sđt
        res_tra_cuu_don = self.client.get(f"/api/ban-hang/khach-hang?tu_khoa={don_vip['ma_don']}")
        self.assertEqual(res_tra_cuu_don.status_code, 200)
        self.assertEqual(res_tra_cuu_don.json["du_lieu"][0]["ma_kh"], "KH003")

        res_tra_cuu_ten = self.client.get("/api/ban-hang/khach-hang?tu_khoa=Tuấn")
        self.assertEqual(res_tra_cuu_ten.status_code, 200)
        self.assertTrue(len(res_tra_cuu_ten.json["du_lieu"]) >= 1)

        # 9. Thống kê doanh thu theo ngày, tháng, năm
        res_tk_ngay = self.client.get("/api/ban-hang/thong-ke/doanh-thu?kieu=ngay")
        self.assertEqual(res_tk_ngay.status_code, 200)
        self.assertTrue(len(res_tk_ngay.json["du_lieu"]) >= 1)
        self.assertEqual(res_tk_ngay.json["du_lieu"][0]["doanh_thu"], 414_000)

        # 10. Thống kê sản phẩm bán chạy (xếp nhiều nhất đến ít nhất)
        res_tk_sp = self.client.get("/api/ban-hang/thong-ke/san-pham")
        self.assertEqual(res_tk_sp.status_code, 200)
        self.assertTrue(len(res_tk_sp.json["du_lieu"]) >= 1)
        self.assertEqual(res_tk_sp.json["du_lieu"][0]["ma_sp"], "SP02")
        self.assertEqual(res_tk_sp.json["du_lieu"][0]["tong_so_luong"], 2)

        # 11. Kiểm tra liên kết dữ liệu với NV_KHO: khi Kho cập nhật, Bán hàng cũng cập nhật ngay
        csrf_kho = self.client.get("/api/xac-thuc/phien").json["du_lieu"]["csrf_token"]
        with closing(ket_noi(self.database)) as conn:
            from kho_ban_hang.repositories.ban_hang.nhan_vien_repository import NhanVienRepository
            from kho_ban_hang.services.kho.dang_ky import dang_ky_kho
            from kho_ban_hang.contracts.kho_dto import DongNhapDTO, PhieuNhapDTO
            parts = dang_ky_kho(conn, CauHinh(self.database), NhanVienRepository(conn).tim_theo_ma)
            phieu = parts.nhap_kho.lap_phieu(
                PhieuNhapDTO("NCC01", date.today(), [DongNhapDTO("SP02", "LO-SYNC-TEST", 10, 150_000)]),
                NhanVienRepository(conn).tim_theo_ma("NV001"),
            )
            parts.nhap_kho.xac_nhan_phieu(phieu.ma_phieu, date.today())

        # Kiểm tra Bán hàng thấy ngay số lượng và nhà cung cấp mới từ kho
        res_sp_moi = self.client.get("/api/ban-hang/san-pham-goi-y")
        self.assertEqual(res_sp_moi.status_code, 200)
        sp02_moi = next(s for s in res_sp_moi.json["du_lieu"] if s["ma_sp"] == "SP02")
        self.assertTrue(sp02_moi["so_kha_dung"] >= 10)
        self.assertEqual(sp02_moi["nha_cung_cap"], "Nhà cung cấp An Phú")

    def test_dang_nhap_chi_can_ten_va_lap_phieu_tu_dong_gan(self):
        # 1. Đăng nhập chỉ cần tên đăng nhập
        csrf = self.client.get("/api/xac-thuc/phien").json["du_lieu"]["csrf_token"]
        login_res = self.client.post("/api/xac-thuc/dang-nhap", json={
            "ten_dang_nhap": "nv_kho",
        }, headers={"X-CSRF-Token": csrf})
        self.assertEqual(login_res.status_code, 200)
        self.assertEqual(login_res.json["du_lieu"]["nguoi_dung"]["vai_tro"], "NV_KHO")

        # 2. Lập phiếu nhập: gõ tên NCC mới, gõ tên SP mới, mã SP và mã lô được máy tự động gán
        csrf = login_res.json["du_lieu"]["csrf_token"]
        from datetime import date
        res_phieu = self.client.post("/api/kho/phieu-nhap", json={
            "ten_ncc": "Nhà cung cấp Việt Nhật",
            "ngay_nhap": date.today().isoformat(),
            "dong": [{
                "ten_sp": "Quạt thông gió mini",
                "so_luong_nhap": 5,
                "gia_nhap": 120_000,
            }]
        }, headers={"X-CSRF-Token": csrf})
        self.assertEqual(res_phieu.status_code, 201)
        data = res_phieu.json["du_lieu"]
        self.assertTrue(data["ma_ncc"].startswith("NCC"))
        self.assertTrue(data["dong"][0]["ma_sp"].startswith("SP"))
        self.assertTrue(data["dong"][0]["ma_lo"].startswith("LO-"))


if __name__ == "__main__":
    unittest.main()
