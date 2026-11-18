from datetime import date

from kho_ban_hang.domain.khach_hang import KhachHang, KhachThuong, KhachVIP


class KhachHangRepository:
    def __init__(self, ket_noi_db):
        self.db = ket_noi_db

    def tim_theo_ma(self, ma_kh) -> KhachHang | None:
        r = self.db.execute("SELECT * FROM khach_hang WHERE ma_kh=?", (ma_kh,)).fetchone()
        if r is None:
            return None
        args = (r["ma_kh"], r["ho_ten"], r["so_dien_thoai"], r["dia_chi"], r["diem_tich_luy"])
        if r["hang"] == "VIP":
            return KhachVIP(*args, ngay_len_hang=date.fromisoformat(r["ngay_len_hang"])
                            if r["ngay_len_hang"] else None)
        return KhachThuong(*args)

    def luu(self, kh: KhachHang) -> None:
        vip = kh.la_vip
        self.db.execute(
            """INSERT INTO khach_hang(ma_kh,ho_ten,so_dien_thoai,dia_chi,diem_tich_luy,hang,ngay_len_hang)
               VALUES (?,?,?,?,?,?,?)
               ON CONFLICT(ma_kh) DO UPDATE SET ho_ten=excluded.ho_ten,
                 so_dien_thoai=excluded.so_dien_thoai, dia_chi=excluded.dia_chi,
                 diem_tich_luy=excluded.diem_tich_luy""",   # hạng chỉ đổi qua nang_hang_vip
            (kh.ma_kh, kh.ho_ten, kh.so_dien_thoai, kh.dia_chi, kh.diem_tich_luy,
             "VIP" if vip else "THUONG",
             kh.ngay_len_hang.isoformat() if vip and kh.ngay_len_hang else None))

    def nang_hang_vip(self, ma_kh: str, ngay: date) -> None:
        self.db.execute("UPDATE khach_hang SET hang='VIP', ngay_len_hang=? WHERE ma_kh=?",
                        (ngay.isoformat(), ma_kh))
