INSERT INTO danh_muc VALUES
    ('DM01', 'Thực phẩm', 'Thực phẩm đóng gói', 'HOAT_DONG'),
    ('DM02', 'Điện tử', 'Thiết bị điện gia dụng', 'HOAT_DONG'),
    ('DM03', 'Thời trang', 'Quần áo', 'HOAT_DONG')
ON CONFLICT DO NOTHING;

INSERT INTO nha_cung_cap VALUES
    ('NCC01', 'Nhà cung cấp An Phú', '', 'Hà Nội', 'HOAT_DONG'),
    ('NCC02', 'Nhà cung cấp Minh Quang', '', 'Hà Nội', 'NGUNG_HOAT_DONG')
ON CONFLICT DO NOTHING;

INSERT INTO san_pham VALUES
    ('SP01', 'Cà phê rang 250 g', 85000, 'gói', 'KINH_DOANH', 'DM01', 'THUC_PHAM', '{"yeu_cau_bao_quan":"Nơi khô ráo"}'),
    ('SP02', 'Đèn bàn LED', 230000, 'chiếc', 'KINH_DOANH', 'DM02', 'DIEN_TU', '{"thoi_gian_bao_hanh":12,"cong_suat":"8.5"}'),
    ('SP03', 'Áo thun cotton', 150000, 'chiếc', 'KINH_DOANH', 'DM03', 'THOI_TRANG', '{"kich_co":"M","chat_lieu":"Cotton"}'),
    ('SP04', 'Trà túi lọc', 42000, 'hộp', 'KINH_DOANH', 'DM01', 'THUC_PHAM', '{"yeu_cau_bao_quan":"Nơi khô ráo"}')
ON CONFLICT DO NOTHING;

INSERT INTO lo_hang VALUES
    ('LO01', 'SP01', date('now','localtime','-15 days'), date('now','localtime','-30 days'), date('now','localtime','+12 days'), 8, 53000),
    ('LO02', 'SP01', date('now','localtime','-7 days'), date('now','localtime','-14 days'), date('now','localtime','+80 days'), 15, 55000),
    ('LO03', 'SP02', date('now','localtime','-5 days'), NULL, NULL, 3, 170000),
    ('LO04', 'SP03', date('now','localtime','-8 days'), NULL, NULL, 12, 90000),
    ('LO05', 'SP04', date('now','localtime','-45 days'), date('now','localtime','-60 days'), date('now','localtime','-1 day'), 6, 28000)
ON CONFLICT DO NOTHING;
