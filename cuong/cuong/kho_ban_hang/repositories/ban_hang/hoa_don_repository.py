from datetime import date

from kho_ban_hang.domain.hoa_don import HoaDon


class HoaDonRepository:
    def __init__(self, ket_noi_db, don_repo, thanh_toan_repo):
        self.db, self.don_repo, self.tt_repo = ket_noi_db, don_repo, thanh_toan_repo

    def luu(self, hd: HoaDon) -> None:
        self.db.execute(
            "INSERT INTO hoa_don VALUES (?,?,?,?,?,?,?)",
            (hd.ma_hd, hd.don_hang.ma_don, hd.thanh_toan.ma_gd, hd.ngay_xuat.isoformat(),
             hd.tong_tien_truoc_giam, hd.tong_giam, hd.tong_thanh_toan))

    def tim_theo_ma_don(self, ma_don) -> HoaDon | None:
        r = self.db.execute("SELECT * FROM hoa_don WHERE ma_don=?", (ma_don,)).fetchone()
        if r is None:
            return None
        don = self.don_repo.tim_theo_ma(ma_don)
        tt = self.tt_repo.tim_theo_ma_don(ma_don, don)
        return HoaDon(r["ma_hd"], don, tt, date.fromisoformat(r["ngay_xuat"]),
                      r["tong_tien_truoc_giam"], r["tong_giam"], r["tong_thanh_toan"])
