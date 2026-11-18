CREATE TABLE IF NOT EXISTS nhan_vien (
    ma_nv TEXT PRIMARY KEY NOT NULL,
    ho_ten TEXT NOT NULL,
    vai_tro TEXT NOT NULL,
    ten_dang_nhap TEXT NOT NULL UNIQUE,
    mat_khau_hash TEXT NOT NULL,
    trang_thai TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS don_hang (
    ma_don TEXT PRIMARY KEY NOT NULL
);

CREATE TABLE IF NOT EXISTS phien_demo (
    ma_bam TEXT PRIMARY KEY NOT NULL,
    ma_nv TEXT NOT NULL REFERENCES nhan_vien(ma_nv) ON DELETE CASCADE,
    het_han_luc TEXT NOT NULL
);
