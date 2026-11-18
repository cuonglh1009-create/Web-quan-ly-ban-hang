CREATE TABLE IF NOT EXISTS danh_muc (
    ma_dm TEXT PRIMARY KEY NOT NULL,
    ten_dm TEXT NOT NULL,
    mo_ta TEXT NOT NULL,
    trang_thai TEXT NOT NULL CHECK (trang_thai IN ('HOAT_DONG', 'NGUNG_HOAT_DONG'))
);

CREATE TABLE IF NOT EXISTS nha_cung_cap (
    ma_ncc TEXT PRIMARY KEY NOT NULL,
    ten_ncc TEXT NOT NULL,
    so_dien_thoai TEXT NOT NULL,
    dia_chi TEXT NOT NULL,
    trang_thai TEXT NOT NULL CHECK (trang_thai IN ('HOAT_DONG', 'NGUNG_HOAT_DONG'))
);

CREATE TABLE IF NOT EXISTS san_pham (
    ma_sp TEXT PRIMARY KEY NOT NULL,
    ten_sp TEXT NOT NULL,
    gia_niem_yet INTEGER NOT NULL CHECK (gia_niem_yet > 0),
    don_vi_tinh TEXT NOT NULL,
    trang_thai TEXT NOT NULL CHECK (trang_thai IN ('KINH_DOANH', 'NGUNG_KINH_DOANH')),
    ma_dm TEXT NOT NULL REFERENCES danh_muc(ma_dm),
    loai TEXT NOT NULL CHECK (loai IN ('DIEN_TU', 'THUC_PHAM', 'THOI_TRANG')),
    thuoc_tinh TEXT NOT NULL CHECK (json_valid(thuoc_tinh))
);

CREATE TABLE IF NOT EXISTS phieu_nhap (
    ma_phieu TEXT PRIMARY KEY NOT NULL,
    ngay_nhap TEXT NOT NULL,
    ma_nv TEXT NOT NULL REFERENCES nhan_vien(ma_nv),
    ma_ncc TEXT NOT NULL REFERENCES nha_cung_cap(ma_ncc),
    trang_thai TEXT NOT NULL CHECK (trang_thai IN ('NHAP', 'DA_XAC_NHAN'))
);

CREATE TABLE IF NOT EXISTS chi_tiet_phieu_nhap (
    ma_phieu TEXT NOT NULL REFERENCES phieu_nhap(ma_phieu) ON DELETE CASCADE,
    stt INTEGER NOT NULL,
    ma_sp TEXT NOT NULL REFERENCES san_pham(ma_sp),
    ma_lo TEXT NOT NULL,
    so_luong_nhap INTEGER NOT NULL CHECK (so_luong_nhap > 0),
    gia_nhap INTEGER NOT NULL CHECK (gia_nhap > 0),
    ngay_san_xuat TEXT,
    han_su_dung TEXT,
    PRIMARY KEY (ma_phieu, stt),
    UNIQUE (ma_phieu, ma_lo)
);

CREATE TABLE IF NOT EXISTS lo_hang (
    ma_lo TEXT PRIMARY KEY NOT NULL,
    ma_sp TEXT NOT NULL REFERENCES san_pham(ma_sp),
    ngay_nhap TEXT NOT NULL,
    ngay_san_xuat TEXT,
    han_su_dung TEXT,
    so_luong_con_lai INTEGER NOT NULL CHECK (so_luong_con_lai >= 0),
    gia_nhap INTEGER NOT NULL CHECK (gia_nhap > 0)
);

CREATE TABLE IF NOT EXISTS giu_hang (
    ma_don TEXT NOT NULL REFERENCES don_hang(ma_don),
    ma_lo TEXT NOT NULL REFERENCES lo_hang(ma_lo),
    so_luong INTEGER NOT NULL CHECK (so_luong > 0),
    PRIMARY KEY (ma_don, ma_lo)
);

CREATE INDEX IF NOT EXISTS idx_lo_hang_ma_sp ON lo_hang(ma_sp);
CREATE INDEX IF NOT EXISTS idx_giu_hang_ma_lo ON giu_hang(ma_lo);
