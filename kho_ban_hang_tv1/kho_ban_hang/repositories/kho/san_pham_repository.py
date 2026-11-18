import json
from dataclasses import asdict

from ...contracts.san_pham_contract import ITraCuuSanPham
from ...domain.enums_kho import LoaiSanPham, TrangThaiSanPham
from ...domain.errors import KhongTimThayError
from ...domain.san_pham import SanPham
from ...services.kho.san_pham_factory import SanPhamFactory


class SanPhamRepository(ITraCuuSanPham):
    def __init__(self, ket_noi_db, danh_muc_repo):
        self.ket_noi_db = ket_noi_db
        self.danh_muc_repo = danh_muc_repo

    def tim_theo_ma(self, ma_sp: str) -> SanPham:
        row = self.ket_noi_db.execute("SELECT * FROM san_pham WHERE ma_sp = ?", (ma_sp,)).fetchone()
        if row is None:
            raise KhongTimThayError(f"Không tìm thấy sản phẩm {ma_sp}.", "ma_sp")
        return self._tao(row)

    def tim_tat_ca(self) -> list[SanPham]:
        return [self._tao(row) for row in self.ket_noi_db.execute("SELECT * FROM san_pham ORDER BY ma_sp")]

    def luu(self, san_pham: SanPham) -> None:
        thuoc_tinh = asdict(san_pham)
        for ten in ("ma_sp", "ten_sp", "gia_niem_yet", "don_vi_tinh", "trang_thai", "danh_muc"):
            del thuoc_tinh[ten]
        self.ket_noi_db.execute(
            """INSERT INTO san_pham VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT (ma_sp) DO UPDATE SET ten_sp=excluded.ten_sp,
               gia_niem_yet=excluded.gia_niem_yet, don_vi_tinh=excluded.don_vi_tinh,
               trang_thai=excluded.trang_thai, ma_dm=excluded.ma_dm, loai=excluded.loai,
               thuoc_tinh=excluded.thuoc_tinh""",
            (san_pham.ma_sp, san_pham.ten_sp, san_pham.gia_niem_yet, san_pham.don_vi_tinh,
             san_pham.trang_thai, san_pham.danh_muc.ma_dm, san_pham.loai, json.dumps(thuoc_tinh, default=str)),
        )

    def _tao(self, row):
        return SanPhamFactory.tao_san_pham(LoaiSanPham(row["loai"]), {
            **json.loads(row["thuoc_tinh"]),
            "ma_sp": row["ma_sp"], "ten_sp": row["ten_sp"], "gia_niem_yet": row["gia_niem_yet"],
            "don_vi_tinh": row["don_vi_tinh"], "trang_thai": TrangThaiSanPham(row["trang_thai"]),
            "danh_muc": self.danh_muc_repo.tim_theo_ma(row["ma_dm"]),
        })
