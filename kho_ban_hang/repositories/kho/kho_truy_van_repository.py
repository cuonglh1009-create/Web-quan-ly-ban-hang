"""Các truy vấn chỉ đọc phục vụ màn hình Kho."""
from datetime import date
import unicodedata


def khop_tu_khoa(noi_dung: str, tu_khoa: str) -> bool:
    def chuan_hoa(value):
        value = unicodedata.normalize("NFD", value.casefold().replace("đ", "d"))
        return " ".join("".join(c for c in value if not unicodedata.combining(c)).split())
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

    def phieu_nhap(self, tu_khoa="", trang_thai=""):
        rows = self.ket_noi_db.execute("""
            SELECT p.ma_phieu, p.ngay_nhap, p.trang_thai, p.ma_ncc, n.ten_ncc,
                   COUNT(ct.stt) AS so_dong,
                   COALESCE(SUM(ct.so_luong_nhap * ct.gia_nhap),0) AS tong_gia_tri
            FROM phieu_nhap p JOIN nha_cung_cap n ON p.ma_ncc=n.ma_ncc
            LEFT JOIN chi_tiet_phieu_nhap ct ON ct.ma_phieu=p.ma_phieu
            GROUP BY p.ma_phieu ORDER BY p.ngay_nhap DESC, p.rowid DESC
        """)
        result = []
        for row in rows:
            p = dict(row)
            if trang_thai and p["trang_thai"] != trang_thai:
                continue
            if khop_tu_khoa(p["ma_phieu"] + " " + p["ten_ncc"], tu_khoa):
                result.append(p)
        return result

    def nha_cung_cap_theo_lo(self):
        rows = self.ket_noi_db.execute("""
            SELECT ct.ma_lo, GROUP_CONCAT(DISTINCT n.ten_ncc) AS ten_ncc
            FROM chi_tiet_phieu_nhap ct JOIN phieu_nhap p ON ct.ma_phieu=p.ma_phieu
            JOIN nha_cung_cap n ON n.ma_ncc=p.ma_ncc
            WHERE p.trang_thai='DA_XAC_NHAN'
            GROUP BY ct.ma_lo
        """)
        return {row["ma_lo"]: row["ten_ncc"] for row in rows}
