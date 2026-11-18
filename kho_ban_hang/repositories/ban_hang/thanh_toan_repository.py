from datetime import datetime

from kho_ban_hang.domain.enums_chung import PhuongThucThanhToan, TrangThaiThanhToan
from kho_ban_hang.domain.thanh_toan import ThanhToan, ThanhToanChuyenKhoan, ThanhToanTienMat


class ThanhToanRepository:
    def __init__(self, ket_noi_db, don_repo=None):
        self.db, self.don_repo = ket_noi_db, don_repo

    def luu(self, tt: ThanhToan) -> None:
        tm = isinstance(tt, ThanhToanTienMat)
        self.db.execute(
            "INSERT INTO thanh_toan VALUES (?,?,?,?,?,?,?,?,?,?)",
            (tt.ma_gd, tt.don_hang.ma_don, tt.so_tien, tt.thoi_diem.isoformat(), tt.trang_thai.value,
             tt.phuong_thuc.value,
             tt.tien_khach_dua if tm else None, tt.tien_thoi if tm else None,
             None if tm else tt.ma_giao_dich_ngan_hang, None if tm else tt.ten_ngan_hang))

    def ton_tai_tham_chieu(self, ten_ngan_hang: str, ma_giao_dich_ngan_hang: str) -> bool:
        return self.db.execute(
            "SELECT 1 FROM thanh_toan WHERE ten_ngan_hang=? AND ma_giao_dich_ngan_hang=?",
            (ten_ngan_hang, ma_giao_dich_ngan_hang)).fetchone() is not None

    def tim_theo_ma_don(self, ma_don, don_hang=None) -> ThanhToan | None:
        """Bổ sung ngoài danh sách đặc tả: HoaDonDTO cần phuong_thuc và tien_thoi."""
        r = self.db.execute("SELECT * FROM thanh_toan WHERE ma_don=? AND trang_thai='THANH_CONG'",
                            (ma_don,)).fetchone()
        if r is None:
            return None
        don = don_hang or self.don_repo.tim_theo_ma(ma_don)
        chung = (r["ma_gd"], don, r["so_tien"], datetime.fromisoformat(r["thoi_diem"]))
        kw = {"trang_thai": TrangThaiThanhToan(r["trang_thai"])}
        if r["phuong_thuc"] == PhuongThucThanhToan.TIEN_MAT.value:
            return ThanhToanTienMat(*chung, tien_khach_dua=r["tien_khach_dua"],
                                    tien_thoi=r["tien_thoi"], **kw)
        return ThanhToanChuyenKhoan(*chung, ma_giao_dich_ngan_hang=r["ma_giao_dich_ngan_hang"],
                                    ten_ngan_hang=r["ten_ngan_hang"], **kw)
