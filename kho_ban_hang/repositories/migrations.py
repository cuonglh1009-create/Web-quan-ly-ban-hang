"""Nâng chỉ mục an toàn, chạy trên CSDL mới hoặc qua CLI có sao lưu."""
from .giao_dich import GiaoDich

CHI_MUC = [
    "CREATE INDEX IF NOT EXISTS idx_don_nhan_vien_ngay ON don_hang(ma_nv,ngay_lap DESC,ma_don DESC)",
    "CREATE INDEX IF NOT EXISTS idx_don_ngay ON don_hang(ngay_lap DESC,ma_don DESC)",
    "CREATE INDEX IF NOT EXISTS idx_don_trang_thai_ngay ON don_hang(trang_thai,ngay_lap DESC,ma_don DESC)",
    "CREATE INDEX IF NOT EXISTS idx_don_khach_ngay ON don_hang(ma_kh,ngay_lap DESC,ma_don DESC)",
    "CREATE INDEX IF NOT EXISTS idx_phieu_trang_thai_ngay ON phieu_nhap(trang_thai,ngay_nhap DESC,ma_phieu DESC)",
    "CREATE INDEX IF NOT EXISTS idx_ct_phieu_lo ON chi_tiet_phieu_nhap(ma_lo,ma_phieu)",
]


def nang_cap_chi_muc(db):
    with GiaoDich(db):
        db.execute("CREATE TABLE IF NOT EXISTS kbh_migrations (ma TEXT PRIMARY KEY, thoi_diem TEXT NOT NULL)")
        for sql in CHI_MUC:
            db.execute(sql)
        db.execute("INSERT OR IGNORE INTO kbh_migrations VALUES ('20261121_read_indexes',datetime('now'))")
