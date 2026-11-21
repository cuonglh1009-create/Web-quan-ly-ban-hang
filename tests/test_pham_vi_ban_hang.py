
"""Hồi quy theo UC01–UC08/QT01–QT12; mọi ghi thử dùng CSDL tạm."""
import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
from datetime import date, timedelta
from unittest.mock import patch
from kho_ban_hang.app import create_app
from kho_ban_hang.config.cau_hinh import CauHinh
from kho_ban_hang.container import Container
from kho_ban_hang.repositories.giao_dich import ket_noi
from kho_ban_hang.services.ban_hang.xac_thuc_service import BoDemThuDangNhap


class PhamViBanHangTest(unittest.TestCase):
    def setUp(self):
        temp=TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.cfg=CauHinh(str(Path(temp.name)/"scope.db"),khoa_bi_mat="scope-regression-key")
        self.app=create_app(self.cfg);self.client=self.app.test_client()
        seeded=self.app.test_cli_runner().invoke(args=["seed","--mat-khau-kho","test-only-pass","--mat-khau-ban-hang","test-only-pass"])
        self.assertEqual(seeded.exit_code,0,seeded.output)
        self.db=ket_noi(self.cfg.duong_dan_csdl);self.addCleanup(self.db.close)
        token=self.client.get("/api/xac-thuc/phien").json["du_lieu"]["csrf_token"]
        login=self.client.post("/api/xac-thuc/dang-nhap",json={"ten_dang_nhap":"nv_ban_hang","mat_khau":"test-only-pass"},headers={"X-CSRF-Token":token})
        self.headers={"X-CSRF-Token":login.json["du_lieu"]["csrf_token"]}

    def post(self,path,data):
        return self.client.post("/api/ban-hang"+path,json=data,headers=self.headers)

    def order(self,**extra):
        result=self.post("/don-hang",{"dong":[{"ma_sp":"SP02","so_luong":1}],**extra})
        self.assertEqual(result.status_code,201,result.json)
        return result.json["du_lieu"]

    def test_truong_khach_sai_kieu_tra_400_khong_ghi_don(self):
        for field in ["ten_kh","sdt_kh","dia_chi_kh"]:
            for value in [123,False,[],{}]:
                with self.subTest(field=field,value=value):
                    response=self.post("/don-hang",{"dong":[{"ma_sp":"SP02","so_luong":1}],field:value})
                    self.assertEqual(response.status_code,400,response.json)
                    self.assertEqual(response.json["loi"]["truong"],field)
        for table in ["don_hang","giu_hang"]:
            self.assertEqual(self.db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0],0)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM khach_hang").fetchone()[0],3)

    def test_gioi_han_va_chuan_hoa_thong_tin_khach(self):
        for field,limit in [("ten_kh",160),("sdt_kh",40),("dia_chi_kh",500)]:
            response=self.post("/don-hang",{"dong":[{"ma_sp":"SP02","so_luong":1}],field:"x"*(limit+1)})
            self.assertEqual(response.status_code,400)
            self.assertEqual(response.json["loi"]["truong"],field)
        don=self.order(ten_kh="  Khách thử  ",sdt_kh=" 0912345678 ",dia_chi_kh=" Hà Nội ")
        row=self.db.execute("SELECT * FROM khach_hang WHERE ma_kh=?",(don["ma_kh"],)).fetchone()
        self.assertEqual((row["ho_ten"],row["so_dien_thoai"],row["dia_chi"]),("Khách thử","0912345678","Hà Nội"))

    def test_khach_le_khong_bat_buoc_thong_tin(self):
        don=self.order(ten_kh=" ",sdt_kh=None,dia_chi_kh="")
        self.assertIsNone(don["ma_kh"])
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM khach_hang").fetchone()[0],3)

    def test_adapter_ban_hang_khong_doc_bang_kho(self):
        from kho_ban_hang.kho_gia import KhoGia,SanPhamGia,tao_san_pham_gia
        from kho_ban_hang.services.ban_hang.ban_hang_service import BanHangService
        class KhongDocSql:
            def execute(self,*args,**kwargs):
                raise AssertionError("Service không được đọc SQL của Kho")
        catalog=SanPhamGia([tao_san_pham_gia("FAKE","Bút thử",1000)])
        service=BanHangService(KhoGia({"FAKE":4}),catalog,None,None,None,KhongDocSql(),self.cfg)
        rows=service.tra_cuu_kho("but")
        self.assertEqual([r["ma_sp"] for r in rows],["FAKE"])
        self.assertEqual(rows[0]["so_kha_dung"],4)
        self.assertEqual(rows[0]["nha_cung_cap"],"Chưa ghi nhận")
        self.assertEqual(service.lay_san_pham_goi_y()[0]["ma_sp"],"FAKE")

    def test_tim_khong_dau_va_chi_doc_ton_nhom_khop(self):
        c=Container(self.cfg,BoDemThuDangNhap(5,900));self.addCleanup(c.dong)
        with patch.object(c.kho,"lay_so_luong_kha_dung_nhieu",wraps=c.kho.lay_so_luong_kha_dung_nhieu) as stock:
            rows=c.ban_hang.tra_cuu_kho(" DEN BAN ")
            self.assertEqual([r["ma_sp"] for r in rows],["SP02"])
            stock.assert_called_once_with(["SP02"])
            self.assertEqual(rows[0]["so_kha_dung"],c.kho.lay_so_luong_kha_dung("SP02"))
        response=self.client.get("/api/ban-hang/tra-cuu-kho?tu_khoa=NOT-FOUND")
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json["du_lieu"],[])

    def test_goi_y_khong_doc_ton_san_pham_ngung_ban(self):
        c=Container(self.cfg,BoDemThuDangNhap(5,900));self.addCleanup(c.dong)
        self.db.execute("UPDATE san_pham SET trang_thai='NGUNG_KINH_DOANH' WHERE ma_sp='SP02'")
        with patch.object(c.kho,"lay_so_luong_kha_dung_nhieu",wraps=c.kho.lay_so_luong_kha_dung_nhieu) as stock:
            rows=c.ban_hang.lay_san_pham_goi_y()
            self.assertNotIn("SP02",[r["ma_sp"] for r in rows])
            self.assertNotIn("SP02",stock.call_args.args[0])

    def test_domain_phieu_khong_nhan_hai_dong_cung_ma_lo(self):
        from kho_ban_hang.domain.phieu_nhap import PhieuNhapKho,ChiTietPhieuNhap
        from kho_ban_hang.domain.lo_hang import LoHang
        from kho_ban_hang.domain.errors_kho import TrungMaLoError
        c=Container(self.cfg,BoDemThuDangNhap(5,900));self.addCleanup(c.dong)
        sp=c.tra_cuu_san_pham.tim_theo_ma("SP02")
        dong=ChiTietPhieuNhap(sp,2,100,LoHang("DUP",sp,date.today(),None,None,2,100))
        nv=c.nhan_vien_repo.tim_theo_ma("NV001")
        ncc=c.thanh_phan_kho.nha_cung_cap_repo.tim_theo_ma("NCC01")
        phieu=PhieuNhapKho("DOMAIN",date.today(),nv,ncc)
        phieu.them_chi_tiet(dong)
        with self.assertRaises(TrungMaLoError) as caught:phieu.them_chi_tiet(dong)
        self.assertEqual(caught.exception.truong,"dong[1].ma_lo")
        self.assertEqual(len(phieu.chi_tiet),1)
        with self.assertRaises(TrungMaLoError):PhieuNhapKho("RELOAD",date.today(),nv,ncc,chi_tiet=[dong,dong])

    def test_hoa_don_co_ten_don_vi_va_giu_gia_chot(self):
        don=self.order();code=don["ma_don"]
        paid=self.post(f"/don-hang/{code}/thanh-toan",{"phuong_thuc":"TIEN_MAT","thong_tin":{"tien_khach_dua":500000}})
        self.assertEqual(paid.status_code,200,paid.json)
        self.db.execute("UPDATE san_pham SET gia_niem_yet=900000 WHERE ma_sp='SP02'")
        invoice=self.client.get(f"/api/ban-hang/don-hang/{code}/hoa-don").json["du_lieu"]
        line=invoice["dong"][0]
        self.assertEqual((line["ten_sp"],line["don_vi_tinh"]),("Đèn bàn LED","chiếc"))
        self.assertEqual((line["don_gia"],line["thanh_tien"],invoice["tong_thanh_toan"]),(230000,230000,230000))
        again=self.post(f"/don-hang/{code}/thanh-toan",{"phuong_thuc":"TIEN_MAT","thong_tin":{"tien_khach_dua":500000}})
        self.assertEqual(again.json["du_lieu"]["ma_hd"],paid.json["du_lieu"]["ma_hd"])
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM hoa_don").fetchone()[0],1)

    def test_ma_hop_le_ngay_cuoi_va_giu_ma_cu_khi_thay_sai(self):
        self.db.execute("UPDATE khuyen_mai SET ngay_ket_thuc=? WHERE ma_km='GIAM10'",(date.today().isoformat(),))
        code=self.order()["ma_don"]
        valid=self.post(f"/don-hang/{code}/khuyen-mai",{"ma_km":"GIAM10"})
        self.assertEqual(valid.status_code,200,valid.json)
        self.assertEqual(valid.json["du_lieu"]["giam_khuyen_mai"],23000)
        invalid=self.post(f"/don-hang/{code}/khuyen-mai",{"ma_km":"NO-SUCH-CODE"})
        self.assertEqual(invalid.status_code,400)
        saved=self.client.get(f"/api/ban-hang/don-hang/{code}").json["du_lieu"]
        self.assertEqual(saved["giam_khuyen_mai"],23000)

    def test_lo_dang_giu_het_han_khong_xuat_va_huy_hoan_giu(self):
        code=self.order()["ma_don"]
        self.db.execute("UPDATE lo_hang SET han_su_dung=? WHERE ma_lo='LO03'",((date.today()-timedelta(days=1)).isoformat(),))
        paid=self.post(f"/don-hang/{code}/thanh-toan",{"phuong_thuc":"TIEN_MAT","thong_tin":{"tien_khach_dua":500000}})
        self.assertEqual(paid.status_code,409,paid.json)
        self.assertEqual(self.db.execute("SELECT so_luong_con_lai FROM lo_hang WHERE ma_lo='LO03'").fetchone()[0],3)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM hoa_don").fetchone()[0],0)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM thanh_toan").fetchone()[0],0)
        self.assertEqual(self.db.execute("SELECT trang_thai FROM don_hang WHERE ma_don=?",(code,)).fetchone()[0],"CHO_THANH_TOAN")
        self.assertEqual(self.db.execute("SELECT so_luong FROM giu_hang WHERE ma_don=?",(code,)).fetchone()[0],1)
        self.assertEqual(self.post(f"/don-hang/{code}/huy",{}).status_code,200)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM giu_hang").fetchone()[0],0)

    def test_diem_chi_doi_qua_hanh_vi_va_khong_nhan_float(self):
        from kho_ban_hang.domain.khach_hang import KhachThuong
        from kho_ban_hang.domain.errors_ban_hang import LoiDuLieu
        kh=KhachThuong("K","Khách","0900","",10)
        with self.assertRaises(AttributeError):kh.diem_tich_luy=-1
        for value in [-1,1.5,True]:
            with self.assertRaises(LoiDuLieu):KhachThuong("K","Khách","","",value)
            with self.assertRaises(LoiDuLieu):kh.cong_diem(value,self.cfg)
        self.assertEqual(kh.diem_tich_luy,10)
        kh.cong_diem(25000,self.cfg)
        self.assertEqual(kh.diem_tich_luy,12)

    def test_tong_hoa_don_bat_bien_va_khop_phep_tinh(self):
        from dataclasses import FrozenInstanceError
        from kho_ban_hang.domain.hoa_don import HoaDon
        from kho_ban_hang.domain.errors_ban_hang import LoiDuLieu
        hd=HoaDon("H",None,None,date.today(),100,20,80)
        with self.assertRaises(FrozenInstanceError):hd.tong_thanh_toan=0
        for amounts in [(100,20,81),(100,101,0),(100.5,0,100.5),(100,-1,101)]:
            with self.assertRaises(LoiDuLieu):HoaDon("BAD",None,None,date.today(),*amounts)
        self.assertEqual(hd.tong_thanh_toan,80)


if __name__=="__main__":
    unittest.main()
