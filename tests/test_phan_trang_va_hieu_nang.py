import unittest
from contextlib import closing
from tempfile import TemporaryDirectory
from pathlib import Path
from datetime import date, timedelta
from dataclasses import FrozenInstanceError
from unittest.mock import patch

from kho_ban_hang.app import create_app
from kho_ban_hang.config.cau_hinh import CauHinh
from kho_ban_hang.repositories.giao_dich import ket_noi
from kho_ban_hang.services.kho.dang_ky import dang_ky_kho
from kho_ban_hang.contracts.kho_dto import BoLocLoDTO
from kho_ban_hang.container import Container
from kho_ban_hang.services.ban_hang.xac_thuc_service import BoDemThuDangNhap


class PhanTrangVaHieuNangTest(unittest.TestCase):
    def setUp(self):
        temp=TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.cfg=CauHinh(str(Path(temp.name)/"test.db"),khoa_bi_mat="regression-test-key")
        self.app=create_app(self.cfg)
        result=self.app.test_cli_runner().invoke(args=["seed","--mat-khau-kho","test-only-pass","--mat-khau-ban-hang","test-only-pass"])
        self.assertEqual(result.exit_code,0,result.output)
        self.client=self.app.test_client()
        self.db=ket_noi(self.cfg.duong_dan_csdl);self.addCleanup(self.db.close)
        self.today=date.today().isoformat()

    def login(self,name):
        token=self.client.get("/api/xac-thuc/phien").json["du_lieu"]["csrf_token"]
        response=self.client.post("/api/xac-thuc/dang-nhap",json={"ten_dang_nhap":name,"mat_khau":"test-only-pass"},headers={"X-CSRF-Token":token})
        self.assertEqual(response.status_code,200)
        return {"X-CSRF-Token":response.json["du_lieu"]["csrf_token"]}

    def test_don_khach_phan_trang_tim_khong_dau_va_quyen(self):
        self.db.execute("INSERT INTO nhan_vien VALUES ('NV003','NV khác','nv_khac','unused','NV_BAN_HANG','HOAT_DONG')")
        self.db.executemany("INSERT INTO don_hang(ma_don,ngay_lap,trang_thai,ma_nv) VALUES (?,?,'CHO_THANH_TOAN','NV002')",[(f"P-{i:03}",self.today) for i in range(31)])
        self.db.execute("INSERT INTO don_hang(ma_don,ngay_lap,trang_thai,ma_nv) VALUES ('OTHER',?,'CHO_THANH_TOAN','NV003')",(self.today,))
        self.login("nv_ban_hang")
        legacy=self.client.get("/api/ban-hang/don-hang").json["du_lieu"]
        self.assertIsInstance(legacy,list);self.assertEqual(len(legacy),31)
        codes=[]
        for page in range(1,5):
            response=self.client.get(f"/api/ban-hang/don-hang?page={page}&page_size=10")
            self.assertEqual(response.status_code,200)
            data=response.json["du_lieu"];self.assertEqual(data["total"],31)
            codes.extend(row["ma_don"] for row in data["items"])
        self.assertEqual(len(set(codes)),31);self.assertNotIn("OTHER",codes)
        self.assertEqual(self.client.get("/api/ban-hang/don-hang/OTHER").status_code,403)
        for query in ["page=0","page=x","page_size=0","page_size=101"]:
            self.assertEqual(self.client.get("/api/ban-hang/don-hang?"+query).status_code,400)
        customers=self.client.get("/api/ban-hang/khach-hang?tu_khoa=NGUYEN&page=1&page_size=10").json["du_lieu"]
        self.assertTrue(any(row["ma_kh"]=="KH001" for row in customers["items"]))
        last=self.client.get("/api/ban-hang/don-hang?page=999&page_size=10").json["du_lieu"]
        self.assertEqual(last["page"],4)
        self.assertEqual(self.client.get("/api/kho/lo-hang?page=1").status_code,403)

    def test_trang_lo_khop_nghiep_vu_va_tong_quan(self):
        exp=(date.today()-timedelta(days=1)).isoformat()
        soon=(date.today()+timedelta(days=2)).isoformat()
        for code,expiry,qty in [("EDGE-EXPIRED",exp,10),("EDGE-SOON",soon,6),("EDGE-ZERO",None,0),("EDGE-OPEN",None,8)]:
            self.db.execute("INSERT INTO lo_hang VALUES (?, 'SP02',?,NULL,?,?,100)",(code,self.today,expiry,qty))
        self.db.execute("INSERT INTO don_hang(ma_don,ngay_lap,trang_thai,ma_nv) VALUES ('RESERVED',?,'CHO_THANH_TOAN','NV002')",(self.today,))
        self.db.execute("INSERT INTO giu_hang VALUES ('RESERVED','EDGE-OPEN',3)")
        kho=dang_ky_kho(self.db,self.cfg,lambda _:None).kho
        expected={row.ma_lo:row for row in kho.tra_cuu_lo_hang(BoLocLoDTO())}
        self.login("nv_kho")
        paged=self.client.get("/api/kho/lo-hang?page=1&page_size=100").json["du_lieu"]
        self.assertEqual(paged["total"],len(expected))
        for row in paged["items"]:
            for field in ("ton_thuc_te","dang_giu","kha_dung"):
                self.assertEqual(row[field],getattr(expected[row["ma_lo"]],field))
        held=self.client.get("/api/kho/lo-hang?page=1&tinh_trang=dang_giu").json["du_lieu"]
        self.assertEqual([row["ma_lo"] for row in held["items"]],["EDGE-OPEN"])
        for status in ["het_han","het_hang","sap_het_han","con_hang","khong_kha_dung"]:
            response=self.client.get("/api/kho/lo-hang?page=1&tinh_trang="+status)
            self.assertEqual(response.status_code,200,response.get_data(as_text=True))
        found=self.client.get("/api/kho/lo-hang?page=1&q=den%20ban").json["du_lieu"]
        self.assertTrue(found["items"]);self.assertTrue(all(row["ma_sp"]=="SP02" for row in found["items"]))
        dashboard=self.client.get("/api/kho/tong-quan").json["du_lieu"]
        totals={}
        for row in expected.values():totals[row.ma_sp]=totals.get(row.ma_sp,0)+row.kha_dung
        self.assertEqual(dashboard["lots"],len(expected))
        self.assertEqual(dashboard["available_products"],sum(value>0 for value in totals.values()))
        self.assertEqual(dashboard["low_products"],len(kho.canh_bao_ton_thap(date.today())))
        for row in dashboard["san_pham"]:self.assertEqual(row["available"],totals.get(row["ma_sp"],0))
        summary=self.client.get("/api/kho/ton-san-pham").json["du_lieu"]
        for row in summary:self.assertEqual(row["available"],totals.get(row["ma_sp"],0))

    def test_phieu_nhap_phan_trang_va_giu_bo_loc(self):
        self.db.executemany("INSERT INTO phieu_nhap VALUES (?,?,'NV001','NCC01','NHAP')",[(f"PAGE-{i:03}",self.today) for i in range(37)])
        self.login("nv_kho")
        response=self.client.get("/kho/phieu-nhap?q=an%20phu&trang_thai=NHAP&page=2&page_size=10")
        self.assertEqual(response.status_code,200)
        text=response.get_data(as_text=True)
        self.assertIn("37 phiếu phù hợp",text);self.assertIn("Trang 2/4",text)
        self.assertIn("page=3",text);self.assertIn("trang_thai=NHAP",text)

    def test_chi_doc_lo_can_thiet_va_doc_don_theo_luot(self):
        self.db.executemany("INSERT INTO lo_hang VALUES (?,'SP03',?,NULL,NULL,1,100)",[(f"UNRELATED-{i}",self.today) for i in range(100)])
        kho=dang_ky_kho(self.db,self.cfg,lambda _:None).kho
        expected=kho.lay_so_luong_kha_dung("SP02")
        with patch.object(kho.lo_hang_repo,"_tao_nhieu",wraps=kho.lo_hang_repo._tao_nhieu) as hydrate:
            self.assertEqual(kho.lay_so_luong_kha_dung_nhieu(["SP02"]),{"SP02":expected})
            for call in hydrate.call_args_list:self.assertTrue(all(row["ma_sp"]=="SP02" for row in call.args[0]))
        self.db.executemany("INSERT INTO san_pham SELECT ?,ten_sp,gia_niem_yet,don_vi_tinh,trang_thai,ma_dm,loai,thuoc_tinh FROM san_pham WHERE ma_sp='SP02'",[(f"LINE-{i}",) for i in range(30)])
        self.db.execute("INSERT INTO don_hang(ma_don,ngay_lap,trang_thai,ma_nv) VALUES ('LINES',?,'CHO_THANH_TOAN','NV002')",(self.today,))
        self.db.executemany("INSERT INTO chi_tiet_don_hang VALUES ('LINES',?,1,100)",[(f"LINE-{i}",) for i in range(30)])
        c=Container(self.cfg,BoDemThuDangNhap(5,900));self.addCleanup(c.dong)
        repo=c.don_repo;queries=[];c.ket_noi.set_trace_callback(queries.append)
        order=repo.tim_theo_ma("LINES");c.ket_noi.set_trace_callback(None)
        self.assertEqual(len(order.chi_tiet),30)
        self.assertLessEqual(sum(q.lstrip().upper().startswith("SELECT") for q in queries),4)

    def test_dong_goi_don_va_gop_dong_giu_gia_chot(self):
        from kho_ban_hang.domain.don_hang import DonHang
        from kho_ban_hang.domain.enums_chung import TrangThaiDonHang
        c=Container(self.cfg,BoDemThuDangNhap(5,900));self.addCleanup(c.dong)
        sp=c.tra_cuu_san_pham.tim_theo_ma("SP02")
        order=DonHang("MODEL",date.today(),TrangThaiDonHang.NHAP,c.nhan_vien_repo.tim_theo_ma("NV002"))
        order.them_chi_tiet(sp,1);price=order.chi_tiet[0].don_gia
        sp.cap_nhat_gia(price+100);order.them_chi_tiet(sp,2)
        self.assertEqual(order.chi_tiet[0].so_luong,3);self.assertEqual(order.chi_tiet[0].don_gia,price)
        with self.assertRaises(AttributeError):order.trang_thai=TrangThaiDonHang.DA_THANH_TOAN
        with self.assertRaises(AttributeError):order.chi_tiet=[]
        with self.assertRaises(FrozenInstanceError):order.chi_tiet[0].so_luong=0

    def test_nang_cap_csdl_co_backup_va_lap_an_toan(self):
        from kho_ban_hang.repositories.migrations import CHI_MUC
        self.db.execute("DROP TABLE kbh_migrations")
        for sql in CHI_MUC:self.db.execute("DROP INDEX "+sql.split("EXISTS ")[1].split(" ON ")[0])
        before=self.db.execute("SELECT COUNT(*) FROM san_pham").fetchone()[0]
        for _ in range(2):
            result=self.app.test_cli_runner().invoke(args=["nang-cap-csdl"])
            self.assertEqual(result.exit_code,0,result.output)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM san_pham").fetchone()[0],before)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM kbh_migrations").fetchone()[0],1)
        self.assertEqual(len(list(Path(self.cfg.duong_dan_csdl).parent.glob("*.backup-*.db"))),2)
        self.assertEqual(self.db.execute("PRAGMA integrity_check").fetchone()[0],"ok")
        plan=self.db.execute("EXPLAIN QUERY PLAN SELECT * FROM lo_hang WHERE ma_sp='SP02'").fetchall()
        self.assertTrue(any("idx_lo_hang_ma_sp" in row["detail"] for row in plan))


if __name__=="__main__":unittest.main()
