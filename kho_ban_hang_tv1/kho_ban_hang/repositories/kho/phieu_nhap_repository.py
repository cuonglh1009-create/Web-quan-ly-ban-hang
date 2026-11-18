from datetime import date
from uuid import uuid4

from ...domain.enums_kho import TrangThaiPhieuNhap
from ...domain.errors import KhongTimThayError
from ...domain.lo_hang import LoHang
from ...domain.phieu_nhap import ChiTietPhieuNhap, PhieuNhapKho


class PhieuNhapRepository:
    def __init__(self, ket_noi_db, san_pham_repo, nha_cung_cap_repo, tim_nhan_vien):
        self.ket_noi_db = ket_noi_db
        self.san_pham_repo = san_pham_repo
        self.nha_cung_cap_repo = nha_cung_cap_repo
        self.tim_nhan_vien = tim_nhan_vien

    def cap_ma_moi(self) -> str:
        return f"PN-{uuid4().hex[:12].upper()}"

    def tim_theo_ma(self, ma_phieu: str) -> PhieuNhapKho:
        row = self.ket_noi_db.execute("SELECT * FROM phieu_nhap WHERE ma_phieu = ?", (ma_phieu,)).fetchone()
        if row is None:
            raise KhongTimThayError(f"Không tìm thấy phiếu {ma_phieu}.", "ma_phieu")
        phieu = PhieuNhapKho(
            row["ma_phieu"], date.fromisoformat(row["ngay_nhap"]), self.tim_nhan_vien(row["ma_nv"]),
            self.nha_cung_cap_repo.tim_theo_ma(row["ma_ncc"]), TrangThaiPhieuNhap(row["trang_thai"]),
        )
        for dong in self.ket_noi_db.execute(
            "SELECT * FROM chi_tiet_phieu_nhap WHERE ma_phieu = ? ORDER BY stt", (ma_phieu,)
        ):
            sp = self.san_pham_repo.tim_theo_ma(dong["ma_sp"])
            lo = LoHang(
                dong["ma_lo"], sp, phieu.ngay_nhap,
                date.fromisoformat(dong["ngay_san_xuat"]) if dong["ngay_san_xuat"] else None,
                date.fromisoformat(dong["han_su_dung"]) if dong["han_su_dung"] else None,
                dong["so_luong_nhap"], dong["gia_nhap"],
            )
            phieu.chi_tiet.append(ChiTietPhieuNhap(sp, dong["so_luong_nhap"], dong["gia_nhap"], lo))
        return phieu

    def luu(self, phieu: PhieuNhapKho) -> None:
        self.ket_noi_db.execute(
            "INSERT INTO phieu_nhap VALUES (?, ?, ?, ?, ?)",
            (phieu.ma_phieu, phieu.ngay_nhap.isoformat(), phieu.nguoi_lap.ma_nv,
             phieu.nha_cung_cap.ma_ncc, phieu.trang_thai),
        )
        self.ket_noi_db.executemany(
            "INSERT INTO chi_tiet_phieu_nhap VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (phieu.ma_phieu, stt, ct.san_pham.ma_sp, ct.lo_hang.ma_lo, ct.so_luong_nhap, ct.gia_nhap,
                 ct.lo_hang.ngay_san_xuat.isoformat() if ct.lo_hang.ngay_san_xuat else None,
                 ct.lo_hang.han_su_dung.isoformat() if ct.lo_hang.han_su_dung else None)
                for stt, ct in enumerate(phieu.chi_tiet, 1)
            ],
        )

    def cap_nhat_trang_thai(self, phieu: PhieuNhapKho) -> None:
        self.ket_noi_db.execute(
            "UPDATE phieu_nhap SET trang_thai = ? WHERE ma_phieu = ?", (phieu.trang_thai, phieu.ma_phieu)
        )
