import unittest
from contextlib import closing
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from kho_ban_hang.app import create_app
from kho_ban_hang.config.cau_hinh import CauHinh
from kho_ban_hang.contracts.kho_contract import ChiTietDatHangDTO
from kho_ban_hang.contracts.kho_dto import BoLocLoDTO
from kho_ban_hang.repositories.giao_dich import ket_noi, GiaoDich
from kho_ban_hang.services.kho.dang_ky import dang_ky_kho


class ToiUuKhoTest(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.db = str(Path(tmp.name) / "test.db")
        self.cfg = CauHinh(self.db, khoa_bi_mat="test-performance-only")
        app = create_app(self.cfg)
        result = app.test_cli_runner().invoke(args=[
            "seed", "--mat-khau-kho", "test-only-pass",
            "--mat-khau-ban-hang", "test-only-pass",
        ])
        self.assertEqual(result.exit_code, 0, result.output)
        self.conn = ket_noi(self.db)
        self.addCleanup(self.conn.close)
        self.kho = dang_ky_kho(self.conn, self.cfg, lambda _: None).kho

    def test_so_truy_van_khong_tang_theo_so_lo(self):
        self.conn.executemany("INSERT INTO lo_hang VALUES (?,?,?,?,?,?,?)", [
            (f"BENCH-{i:03}", "SP02", date.today().isoformat(), None, None, 2, 100)
            for i in range(100)
        ])
        for operation, limit in [
            (lambda: self.kho.tra_cuu_lo_hang(BoLocLoDTO()), 2),
            (lambda: self.kho.chon_lo_xuat("SP02", 150, date.today()), 3),
        ]:
            queries = []
            self.conn.set_trace_callback(queries.append)
            try:
                rows = operation()
            finally:
                self.conn.set_trace_callback(None)
            self.assertTrue(rows)
            self.assertLessEqual(sum(q.lstrip().upper().startswith("SELECT") for q in queries), limit)

    def test_fefo_bo_qua_het_han_va_tru_dang_giu(self):
        today = date.today()
        self.conn.execute("UPDATE lo_hang SET so_luong_con_lai=0 WHERE ma_sp='SP01'")
        batches = [
            ("EXPIRED", -1, 20), ("SOON", 2, 4),
            ("LATER", 20, 8), ("NO-EXPIRY", None, 10),
        ]
        for code, days, qty in batches:
            expiry = (today + timedelta(days=days)).isoformat() if days is not None else None
            self.conn.execute("INSERT INTO lo_hang VALUES (?,?,?,?,?,?,?)",
                              (code, "SP01", today.isoformat(), today.isoformat(), expiry, qty, 100))
        self.conn.execute("""INSERT INTO don_hang(ma_don,ngay_lap,trang_thai,ma_nv)
                             VALUES ('TEST-HOLD',?,'CHO_THANH_TOAN','NV002')""", (today.isoformat(),))
        self.conn.execute("INSERT INTO giu_hang VALUES ('TEST-HOLD','SOON',3)")
        result = self.kho.chon_lo_xuat("SP01", 10, today)
        self.assertEqual([(lo.ma_lo, qty) for lo, qty in result],
                         [("SOON", 1), ("LATER", 8), ("NO-EXPIRY", 1)])

    def test_rollback_va_khong_luu_cache_ton(self):
        self.conn.execute("""INSERT INTO don_hang(ma_don,ngay_lap,trang_thai,ma_nv)
                             VALUES ('TEST-ROLLBACK',?,'CHO_THANH_TOAN','NV002')""",
                          (date.today().isoformat(),))
        before = self.kho.lay_so_luong_kha_dung("SP02")
        with self.assertRaisesRegex(RuntimeError, "rollback"):
            with GiaoDich(self.conn):
                self.kho.giu_hang("TEST-ROLLBACK", [ChiTietDatHangDTO("SP02", 1)])
                self.assertEqual(self.kho.lay_so_luong_kha_dung("SP02"), before - 1)
                raise RuntimeError("rollback")
        self.assertEqual(self.kho.lay_so_luong_kha_dung("SP02"), before)
        with GiaoDich(self.conn):
            self.kho.giu_hang("TEST-ROLLBACK", [ChiTietDatHangDTO("SP02", 1)])
            self.kho.giu_hang("TEST-ROLLBACK", [ChiTietDatHangDTO("SP02", 1)])
        self.assertEqual(self.kho.lay_so_luong_kha_dung("SP02"), before - 1)
        with GiaoDich(self.conn):
            self.kho.xac_nhan_xuat_kho("TEST-ROLLBACK")
        self.assertEqual(self.kho.lay_so_luong_kha_dung("SP02"), before - 1)

    def test_phieu_nhieu_dong_doc_san_pham_theo_luot(self):
        from kho_ban_hang.repositories.ban_hang.nhan_vien_repository import NhanVienRepository
        from kho_ban_hang.contracts.kho_dto import PhieuNhapDTO, DongNhapDTO
        nv = NhanVienRepository(self.conn).tim_theo_ma
        nhap = dang_ky_kho(self.conn, self.cfg, nv).nhap_kho
        phieu = nhap.lap_phieu(PhieuNhapDTO("NCC01", date.today(), [
            DongNhapDTO("SP02", f"RECEIPT-{i}", 2, 100) for i in range(100)
        ]), nv("NV001"))
        queries = []
        self.conn.set_trace_callback(queries.append)
        try:
            actual = nhap.tra_cuu_phieu(phieu.ma_phieu)
        finally:
            self.conn.set_trace_callback(None)
        self.assertEqual(len(actual.chi_tiet), 100)
        self.assertLessEqual(sum(q.lstrip().upper().startswith("SELECT") for q in queries), 5)

    def test_dong_phieu_khong_duoc_mau_thuan_voi_lo(self):
        from dataclasses import replace
        from kho_ban_hang.domain.lo_hang import LoHang
        from kho_ban_hang.domain.phieu_nhap import ChiTietPhieuNhap
        from kho_ban_hang.domain.errors import DuLieuKhongHopLeError
        sp = self.kho.san_pham_repo.tim_theo_ma("SP02")
        khac = self.kho.san_pham_repo.tim_theo_ma("SP03")
        lo = LoHang("TEST-ENTITY", sp, date.today(), None, None, 2, 100)
        dong = ChiTietPhieuNhap(sp, 2, 100, lo)
        dong.kiem_tra_hop_le(date.today())
        for bad in [
            replace(dong, san_pham=khac), replace(dong, so_luong_nhap=3),
            replace(dong, gia_nhap=200),
            replace(dong, lo_hang=replace(lo, ngay_nhap=date.today()-timedelta(days=1))),
        ]:
            with self.subTest(bad=bad):
                with self.assertRaises(DuLieuKhongHopLeError):
                    bad.kiem_tra_hop_le(date.today())

    def test_hai_don_dong_thoi_khong_giu_vuot_ton(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from kho_ban_hang.domain.errors_kho import KhongDuTonKhoError
        today = date.today().isoformat()
        self.conn.execute("UPDATE lo_hang SET so_luong_con_lai=0 WHERE ma_sp='SP02'")
        self.conn.execute("INSERT INTO lo_hang VALUES ('CONCURRENT','SP02',?,NULL,NULL,2,100)", (today,))
        self.conn.executemany(
            "INSERT INTO don_hang(ma_don,ngay_lap,trang_thai,ma_nv) VALUES (?,?,'CHO_THANH_TOAN','NV002')",
            [("PARALLEL-1", today), ("PARALLEL-2", today)],
        )
        barrier = Barrier(2)
        def reserve(code):
            with closing(ket_noi(self.db)) as conn:
                kho = dang_ky_kho(conn, self.cfg, lambda _: None).kho
                barrier.wait(timeout=5)
                try:
                    with GiaoDich(conn):
                        kho.giu_hang(code, [ChiTietDatHangDTO("SP02", 2)])
                    return "ok"
                except KhongDuTonKhoError:
                    return "insufficient"
        with ThreadPoolExecutor(max_workers=2) as pool:
            result = list(pool.map(reserve, ["PARALLEL-1", "PARALLEL-2"]))
        self.assertCountEqual(result, ["ok", "insufficient"])
        self.assertEqual(self.conn.execute(
            "SELECT SUM(so_luong) FROM giu_hang WHERE ma_lo='CONCURRENT'"
        ).fetchone()[0], 2)


if __name__ == "__main__":
    unittest.main()
