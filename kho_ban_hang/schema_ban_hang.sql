PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS nhan_vien (
  ma_nv TEXT PRIMARY KEY,
  ho_ten TEXT NOT NULL,
  ten_dang_nhap TEXT NOT NULL UNIQUE COLLATE NOCASE,
  mat_khau_hash TEXT NOT NULL,
  vai_tro TEXT NOT NULL CHECK (vai_tro IN ('NV_KHO','NV_BAN_HANG')),
  trang_thai TEXT NOT NULL DEFAULT 'HOAT_DONG' CHECK (trang_thai IN ('HOAT_DONG','NGUNG_HOAT_DONG'))
);

CREATE TABLE IF NOT EXISTS phien_lam_viec (
  ma_bam TEXT PRIMARY KEY,
  ma_nv TEXT REFERENCES nhan_vien(ma_nv),
  thoi_diem_dang_nhap TEXT,
  het_han_luc TEXT NOT NULL,
  csrf_token TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS khach_hang (
  ma_kh TEXT PRIMARY KEY,
  ho_ten TEXT NOT NULL,
  so_dien_thoai TEXT NOT NULL DEFAULT '',
  dia_chi TEXT NOT NULL DEFAULT '',
  diem_tich_luy INTEGER NOT NULL DEFAULT 0 CHECK (diem_tich_luy >= 0),
  hang TEXT NOT NULL DEFAULT 'THUONG' CHECK (hang IN ('THUONG','VIP')),
  ngay_len_hang TEXT
);

CREATE TABLE IF NOT EXISTS khuyen_mai (
  ma_km TEXT PRIMARY KEY,
  ten_km TEXT NOT NULL,
  loai TEXT NOT NULL CHECK (loai IN ('PHAN_TRAM','TIEN_MAT')),
  ngay_bat_dau TEXT NOT NULL,
  ngay_ket_thuc TEXT NOT NULL,
  gia_tri_don_toi_thieu INTEGER NOT NULL DEFAULT 0,
  trang_thai TEXT NOT NULL DEFAULT 'HOAT_DONG' CHECK (trang_thai IN ('HOAT_DONG','NGUNG')),
  phan_tram_giam TEXT,
  giam_toi_da INTEGER,
  so_tien_giam INTEGER
);

CREATE TABLE IF NOT EXISTS bo_dem_ma (ten TEXT PRIMARY KEY, gia_tri INTEGER NOT NULL);

CREATE TABLE IF NOT EXISTS don_hang (
  ma_don TEXT PRIMARY KEY,
  ngay_lap TEXT NOT NULL,
  trang_thai TEXT NOT NULL CHECK (trang_thai IN ('NHAP','CHO_THANH_TOAN','DA_THANH_TOAN','DA_HUY')),
  ma_nv TEXT NOT NULL REFERENCES nhan_vien(ma_nv),
  ma_kh TEXT REFERENCES khach_hang(ma_kh),
  ma_km TEXT REFERENCES khuyen_mai(ma_km),
  giam_hang_khach INTEGER NOT NULL DEFAULT 0 CHECK (giam_hang_khach >= 0),
  giam_khuyen_mai INTEGER NOT NULL DEFAULT 0 CHECK (giam_khuyen_mai >= 0)
);

CREATE TABLE IF NOT EXISTS chi_tiet_don_hang (
  ma_don TEXT NOT NULL REFERENCES don_hang(ma_don),
  ma_sp TEXT NOT NULL,
  so_luong INTEGER NOT NULL CHECK (so_luong > 0),
  don_gia INTEGER NOT NULL CHECK (don_gia >= 0),   -- giá đã chốt khi lập đơn
  PRIMARY KEY (ma_don, ma_sp)
);

CREATE TABLE IF NOT EXISTS thanh_toan (
  ma_gd TEXT PRIMARY KEY,
  ma_don TEXT NOT NULL REFERENCES don_hang(ma_don),
  so_tien INTEGER NOT NULL CHECK (so_tien >= 0),
  thoi_diem TEXT NOT NULL,
  trang_thai TEXT NOT NULL CHECK (trang_thai IN ('THANH_CONG','THAT_BAI')),
  phuong_thuc TEXT NOT NULL CHECK (phuong_thuc IN ('TIEN_MAT','CHUYEN_KHOAN')),
  tien_khach_dua INTEGER,
  tien_thoi INTEGER,
  ma_giao_dich_ngan_hang TEXT,
  ten_ngan_hang TEXT
);
-- mỗi đơn tối đa một giao dịch thành công
CREATE UNIQUE INDEX IF NOT EXISTS ux_thanh_toan_don_thanh_cong
  ON thanh_toan(ma_don) WHERE trang_thai = 'THANH_CONG';
-- mã tham chiếu duy nhất theo từng ngân hàng
CREATE UNIQUE INDEX IF NOT EXISTS ux_thanh_toan_tham_chieu
  ON thanh_toan(ten_ngan_hang, ma_giao_dich_ngan_hang) WHERE ma_giao_dich_ngan_hang IS NOT NULL;

CREATE TABLE IF NOT EXISTS hoa_don (
  ma_hd TEXT PRIMARY KEY,
  ma_don TEXT NOT NULL UNIQUE REFERENCES don_hang(ma_don),   -- một hóa đơn mỗi đơn
  ma_gd TEXT NOT NULL REFERENCES thanh_toan(ma_gd),
  ngay_xuat TEXT NOT NULL,
  tong_tien_truoc_giam INTEGER NOT NULL,
  tong_giam INTEGER NOT NULL,
  tong_thanh_toan INTEGER NOT NULL
);
