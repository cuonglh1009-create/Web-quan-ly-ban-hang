"""Chạy bằng python scripts/benchmark.py --output <file.json> [--paged]. Chỉ ghi CSDL tạm."""
import argparse,json,time,statistics,sys
sys.path.insert(0,str(__import__("pathlib").Path(__file__).resolve().parents[1]))
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import date
from kho_ban_hang.app import create_app
from kho_ban_hang.config.cau_hinh import CauHinh
from kho_ban_hang.container import Container
from kho_ban_hang.services.ban_hang.xac_thuc_service import BoDemThuDangNhap
from kho_ban_hang.repositories.kho.kho_truy_van_repository import KhoTruyVanRepository

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",required=True)
    parser.add_argument("--paged",action="store_true")
    parser.add_argument("--only",default="")
    args=parser.parse_args()
    with TemporaryDirectory() as tmp:
        cfg=CauHinh(str(Path(tmp)/"benchmark.db"),khoa_bi_mat="benchmark-key-only")
        app=create_app(cfg)
        seeded=app.test_cli_runner().invoke(args=["seed","--mat-khau-kho","test-only-pass","--mat-khau-ban-hang","test-only-pass"])
        assert seeded.exit_code==0,seeded.output
        c=Container(cfg,BoDemThuDangNhap(5,900));db=c.ket_noi;today=date.today().isoformat()
        try:
            db.execute("BEGIN")
            db.executemany("INSERT INTO san_pham SELECT ?,ten_sp,gia_niem_yet,don_vi_tinh,trang_thai,ma_dm,loai,thuoc_tinh FROM san_pham WHERE ma_sp='SP02'",[(f"PERF-{i:04}",) for i in range(996)])
            codes=[row[0] for row in db.execute("SELECT ma_sp FROM san_pham ORDER BY ma_sp")]
            db.executemany("INSERT INTO lo_hang VALUES (?,?,?,NULL,NULL,10,100)",[(f"BENCH-LOT-{i:05}",codes[i%1000],today) for i in range(9995)])
            db.executemany("INSERT INTO don_hang(ma_don,ngay_lap,trang_thai,ma_nv) VALUES (?,?,'CHO_THANH_TOAN','NV002')",[(f"BENCH-ORDER-{i:04}",today) for i in range(1000)])
            db.executemany("INSERT INTO chi_tiet_don_hang VALUES ('BENCH-ORDER-0000',?,1,100)",[(code,) for code in codes])
            db.executemany("INSERT INTO khach_hang(ma_kh,ho_ten,so_dien_thoai,dia_chi,diem_tich_luy,hang) VALUES (?,?,?,'Hà Nội',0,'THUONG')",[(f"BENCH-KH-{i:04}",f"Khách kiểm thử {i}","0900000000") for i in range(1000)])
            db.executemany("INSERT INTO phieu_nhap VALUES (?,?,'NV001','NCC01','NHAP')",[(f"BENCH-PN-{i:04}",today) for i in range(1000)])
            db.commit()
            paged={"page":1,"page_size":20} if args.paged else {}
            operations={
                "selected_stock":lambda:c.kho.lay_so_luong_kha_dung_nhieu(["SP02"]),
                "order_1000_lines":lambda:c.don_repo.tim_theo_ma("BENCH-ORDER-0000"),
                "orders":lambda:c.don_repo.lay_danh_sach(**paged),
                "customers":lambda:c.khach_repo.tim_tat_ca(**paged),
                "receipts":lambda:KhoTruyVanRepository(db).phieu_nhap(**paged),
                "lots":lambda:KhoTruyVanRepository(db).lo_hang(**paged) if args.paged else c.kho.tra_cuu_lo_hang(__import__("kho_ban_hang.contracts.kho_dto",fromlist=["BoLocLoDTO"]).BoLocLoDTO()),
            }
            result={"dataset":{"products":1000,"lots":10000,"orders":1000,"customers":1003,"receipts":1000},"paged":args.paged,"measurements":{}}
            for name,op in operations.items():
                if args.only and name!=args.only:continue
                times=[];queries=[];value=None
                for repeat in range(3):
                    traced=[];db.set_trace_callback(traced.append)
                    start=time.perf_counter();value=op();times.append((time.perf_counter()-start)*1000)
                    db.set_trace_callback(None);queries=traced
                data=value if isinstance(value,(list,dict)) else {"ma_don":value.ma_don,"dong":[{"ma_sp":ct.san_pham.ma_sp,"so_luong":ct.so_luong} for ct in value.chi_tiet]}
                result["measurements"][name]={"median_ms":round(statistics.median(times),3),"selects":sum(q.lstrip().upper().startswith(("SELECT","WITH")) for q in queries),"json_bytes":len(json.dumps(data,ensure_ascii=False,default=lambda v: __import__("dataclasses").asdict(v) if __import__("dataclasses").is_dataclass(v) else str(v)).encode()),"rows":len(value["items"]) if isinstance(value,dict) and "items" in value else len(value) if isinstance(value,list) else None}
            result["query_plans"]=[dict(r) for r in db.execute("EXPLAIN QUERY PLAN SELECT * FROM lo_hang WHERE ma_sp=?",("SP02",))]
            result["query_plans_owner_orders"]=[dict(r) for r in db.execute("EXPLAIN QUERY PLAN SELECT ma_don FROM don_hang WHERE ma_nv=? ORDER BY ngay_lap DESC,ma_don DESC LIMIT 20",("NV002",))]
            result["python"]=sys.version
            Path(args.output).parent.mkdir(parents=True,exist_ok=True)
            Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
            print(json.dumps(result,ensure_ascii=False))
        finally:c.dong()
if __name__=="__main__":main()
