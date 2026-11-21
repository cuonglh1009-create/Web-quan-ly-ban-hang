"""Các truy vấn chỉ đọc phục vụ màn hình Kho."""
from datetime import date, timedelta
from ..phan_trang import lay_trang
from ..tim_kiem import chuan_hoa


def khop_tu_khoa(noi_dung: str, tu_khoa: str) -> bool:
    return chuan_hoa(tu_khoa) in chuan_hoa(noi_dung)


class KhoTruyVanRepository:
    def __init__(self, ket_noi_db):
        self.ket_noi_db = ket_noi_db

    def san_pham(self):
        return [dict(row) for row in self.ket_noi_db.execute("""
            SELECT ma_sp, ten_sp, gia_niem_yet, don_vi_tinh, trang_thai, loai
            FROM san_pham ORDER BY ten_sp, ma_sp
        """)]

    def nha_cung_cap(self):
        return [dict(row) for row in self.ket_noi_db.execute(
            "SELECT ma_ncc, ten_ncc, trang_thai FROM nha_cung_cap ORDER BY ten_ncc"
        )]

    def phieu_nhap(self, tu_khoa="", trang_thai="", page=None, page_size=20):
        where, params = [], []
        if trang_thai:
            where.append("p.trang_thai = ?"); params.append(trang_thai)
        if tu_khoa.strip():
            where.append("instr(chuan_hoa(p.ma_phieu || ' ' || n.ten_ncc), ?) > 0")
            params.append(chuan_hoa(tu_khoa))
        sql = """
            SELECT p.ma_phieu, p.ngay_nhap, p.trang_thai, p.ma_ncc, n.ten_ncc,
                   COUNT(ct.stt) AS so_dong,
                   COALESCE(SUM(ct.so_luong_nhap * ct.gia_nhap),0) AS tong_gia_tri
            FROM phieu_nhap p JOIN nha_cung_cap n ON p.ma_ncc=n.ma_ncc
            LEFT JOIN chi_tiet_phieu_nhap ct ON ct.ma_phieu=p.ma_phieu
        """ + (" WHERE " + " AND ".join(where) if where else "") + " GROUP BY p.ma_phieu ORDER BY p.ngay_nhap DESC, p.rowid DESC"
        if page is not None:
            return lay_trang(self.ket_noi_db, sql, params, page, page_size)
        return [dict(row) for row in self.ket_noi_db.execute(sql, params)]

    def lo_hang(self, q="", tinh_trang="", ma_lo=None, ma_sp=None, page=1, page_size=20,
                ngay=None, so_ngay_canh_bao=30):
        ngay = ngay or date.today()
        today = ngay.isoformat(); warning = (ngay+timedelta(days=so_ngay_canh_bao)).isoformat()
        inner_where, params = [], []
        for col, value in (("ma_lo", ma_lo), ("ma_sp", ma_sp)):
            if value:
                inner_where.append("lo." + col + " = ?");params.append(value)
        base = """SELECT lo.*, sp.ten_sp, sp.trang_thai,
                   COALESCE((SELECT SUM(g.so_luong) FROM giu_hang g WHERE g.ma_lo=lo.ma_lo),0) AS dang_giu,
                   COALESCE((SELECT GROUP_CONCAT(DISTINCT n.ten_ncc)
                       FROM chi_tiet_phieu_nhap ct JOIN phieu_nhap p ON p.ma_phieu=ct.ma_phieu
                       JOIN nha_cung_cap n ON n.ma_ncc=p.ma_ncc
                       WHERE ct.ma_lo=lo.ma_lo AND p.trang_thai='DA_XAC_NHAN'),'Chưa ghi nhận') AS nha_cung_cap
                   FROM lo_hang lo JOIN san_pham sp ON sp.ma_sp=lo.ma_sp"""
        if inner_where:
            base += " WHERE " + " AND ".join(inner_where)
        sql = """SELECT ma_lo,ma_sp,ten_sp,ngay_nhap,ngay_san_xuat,han_su_dung,nha_cung_cap,
                  so_luong_con_lai AS ton_thuc_te,dang_giu,
                  CASE WHEN trang_thai='KINH_DOANH' AND (han_su_dung IS NULL OR han_su_dung>=?)
                       THEN so_luong_con_lai-dang_giu ELSE 0 END AS kha_dung
                  FROM (""" + base + ")"
        # Dấu ? của SELECT ngoài đứng trước các tham số của SELECT trong.
        params = [today, *params]
        filters = {
            'het_han': ("han_su_dung < ?", [today]),
            'het_hang': ("(han_su_dung IS NULL OR han_su_dung>=?) AND ton_thuc_te=0", [today]),
            'sap_het_han': ("ton_thuc_te>0 AND han_su_dung>=? AND han_su_dung<=?", [today, warning]),
            'con_hang': ("ton_thuc_te>0 AND kha_dung>0 AND (han_su_dung IS NULL OR han_su_dung>?)", [warning]),
            'khong_kha_dung': ("ton_thuc_te>0 AND kha_dung=0 AND (han_su_dung IS NULL OR han_su_dung>?)", [warning]),
            'dang_giu': ("dang_giu>0", []),
        }
        clauses = []
        if q.strip():
            clauses.append("instr(chuan_hoa(ma_lo || ' ' || ma_sp || ' ' || ten_sp || ' ' || nha_cung_cap),?)>0")
            params.append(chuan_hoa(q))
        if tinh_trang in filters:
            condition, values = filters[tinh_trang];clauses.append(condition);params.extend(values)
        # Bọc ngoài để dùng được các alias khả dụng và nhà cung cấp trong bộ lọc.
        sql = "SELECT * FROM (" + sql + ")" + (" WHERE " + " AND ".join(clauses) if clauses else "") + " ORDER BY ma_lo"
        return lay_trang(self.ket_noi_db, sql, params, page, page_size)


    def tong_quan(self, nguong=5, so_ngay=30, ngay=None):
        own_snapshot = not self.ket_noi_db.in_transaction
        if own_snapshot:
            self.ket_noi_db.execute("BEGIN")
        try:
            return self._tong_quan(nguong, so_ngay, ngay)
        finally:
            if own_snapshot:
                self.ket_noi_db.rollback()

    def _tong_quan(self, nguong=5, so_ngay=30, ngay=None):
        ngay = ngay or date.today()
        today = ngay.isoformat()
        end = (ngay+timedelta(days=so_ngay)).isoformat()
        cte = """WITH giu AS (SELECT ma_lo,SUM(so_luong) AS sl FROM giu_hang GROUP BY ma_lo),
            ton AS (
              SELECT sp.ma_sp,sp.ten_sp,sp.don_vi_tinh,sp.trang_thai,
                COALESCE(SUM(lo.so_luong_con_lai),0) AS actual,
                COALESCE(SUM(g.sl),0) AS reserved,
                COALESCE(SUM(CASE WHEN sp.trang_thai='KINH_DOANH'
                    AND (lo.han_su_dung IS NULL OR lo.han_su_dung>=?)
                    THEN lo.so_luong_con_lai-COALESCE(g.sl,0) ELSE 0 END),0) AS available
              FROM san_pham sp LEFT JOIN lo_hang lo ON lo.ma_sp=sp.ma_sp
              LEFT JOIN giu g ON g.ma_lo=lo.ma_lo GROUP BY sp.ma_sp) """
        totals = dict(self.ket_noi_db.execute(cte + """SELECT
            COUNT(CASE WHEN available>0 THEN 1 END) AS available_products,
            COUNT(CASE WHEN trang_thai='KINH_DOANH' AND available<? THEN 1 END) AS low_products
            FROM ton""", (today,nguong)).fetchone())
        stock = [dict(r) for r in self.ket_noi_db.execute(cte +
            "SELECT * FROM ton ORDER BY ten_sp,ma_sp LIMIT 8", (today,))]
        low = [dict(r) for r in self.ket_noi_db.execute(cte +
            "SELECT * FROM ton WHERE trang_thai='KINH_DOANH' AND available<? ORDER BY available,ma_sp LIMIT 2", (today,nguong))]
        counts = self.ket_noi_db.execute("""SELECT COUNT(*) AS lots,
            COUNT(CASE WHEN EXISTS(SELECT 1 FROM giu_hang g WHERE g.ma_lo=lo.ma_lo) THEN 1 END) AS reserved_lots
            FROM lo_hang lo""").fetchone()
        expiring = [dict(r) for r in self.ket_noi_db.execute("""SELECT lo.ma_lo,lo.ma_sp,lo.han_su_dung,sp.ten_sp
            FROM lo_hang lo JOIN san_pham sp ON sp.ma_sp=lo.ma_sp
            WHERE lo.so_luong_con_lai>0 AND lo.han_su_dung>=? AND lo.han_su_dung<=?
            ORDER BY lo.han_su_dung,lo.ma_lo LIMIT 2""", (today,end))]
        for row in low:
            row["noi_dung"] = f'{row["ten_sp"]} còn {row["available"]} {row["don_vi_tinh"]} khả dụng.'
        for row in expiring:
            days = (date.fromisoformat(row["han_su_dung"])-ngay).days
            row["noi_dung"] = f'Lô {row["ma_lo"]} còn {days} ngày đến hạn.'
        return {**totals, **dict(counts), "san_pham":stock,
                "ton_thap":low,"sap_het_han":expiring}

    def ton_san_pham(self, ngay=None):
        """Tổng khả dụng theo sản phẩm; không tải/hydrate từng lô lên trình duyệt."""
        today = (ngay or date.today()).isoformat()
        return [dict(row) for row in self.ket_noi_db.execute("""
            WITH giu AS (SELECT ma_lo,SUM(so_luong) AS sl FROM giu_hang GROUP BY ma_lo)
            SELECT sp.ma_sp,COALESCE(SUM(
                CASE WHEN sp.trang_thai='KINH_DOANH'
                  AND (lo.han_su_dung IS NULL OR lo.han_su_dung>=?)
                THEN lo.so_luong_con_lai-COALESCE(g.sl,0) ELSE 0 END),0) AS available
            FROM san_pham sp LEFT JOIN lo_hang lo ON lo.ma_sp=sp.ma_sp
            LEFT JOIN giu g ON g.ma_lo=lo.ma_lo GROUP BY sp.ma_sp ORDER BY sp.ma_sp
        """, (today,))]

    def nha_cung_cap_theo_lo(self):
        rows = self.ket_noi_db.execute("""
            SELECT ct.ma_lo, GROUP_CONCAT(DISTINCT n.ten_ncc) AS ten_ncc
            FROM chi_tiet_phieu_nhap ct JOIN phieu_nhap p ON ct.ma_phieu=p.ma_phieu
            JOIN nha_cung_cap n ON n.ma_ncc=p.ma_ncc
            WHERE p.trang_thai='DA_XAC_NHAN'
            GROUP BY ct.ma_lo
        """)
        return {row["ma_lo"]: row["ten_ncc"] for row in rows}
