from datetime import datetime

from kho_ban_hang.contracts.xac_thuc_contract import PhienLamViec


def _dt(s):
    return datetime.fromisoformat(s) if s else None


class PhienLamViecRepository:
    def __init__(self, ket_noi_db):
        self.db = ket_noi_db

    def tim_theo_ma_bam(self, ma_bam):
        r = self.db.execute("SELECT * FROM phien_lam_viec WHERE ma_bam=?", (ma_bam,)).fetchone()
        if r is None:
            return None
        return PhienLamViec(r["ma_bam"], r["ma_nv"], _dt(r["thoi_diem_dang_nhap"]),
                            _dt(r["het_han_luc"]), r["csrf_token"])

    def luu(self, p: PhienLamViec) -> None:
        self.db.execute(
            """INSERT INTO phien_lam_viec VALUES (?,?,?,?,?)
               ON CONFLICT(ma_bam) DO UPDATE SET ma_nv=excluded.ma_nv,
                 thoi_diem_dang_nhap=excluded.thoi_diem_dang_nhap,
                 het_han_luc=excluded.het_han_luc, csrf_token=excluded.csrf_token""",
            (p.ma_bam, p.ma_nv, p.thoi_diem_dang_nhap and p.thoi_diem_dang_nhap.isoformat(),
             p.het_han_luc.isoformat(), p.csrf_token))

    def thu_hoi(self, ma_bam) -> None:
        self.db.execute("DELETE FROM phien_lam_viec WHERE ma_bam=?", (ma_bam,))

    def xoa_het_han(self, bay_gio: datetime) -> None:
        self.db.execute("DELETE FROM phien_lam_viec WHERE het_han_luc<=?", (bay_gio.isoformat(),))
