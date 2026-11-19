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


if __name__ == "__main__":
    unittest.main()
