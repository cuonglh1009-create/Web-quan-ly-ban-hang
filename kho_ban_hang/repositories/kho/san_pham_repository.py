import json
from dataclasses import asdict

from ...contracts.san_pham_contract import ITraCuuSanPham
from ...domain.enums_kho import LoaiSanPham, TrangThaiSanPham
from ...domain.errors import KhongTimThayError
from ...domain.danh_muc import DanhMuc
from ...domain.enums_kho import TrangThaiDanhMuc
from ...domain.san_pham import SanPham
from ...domain.san_pham_factory import SanPhamFactory


class SanPhamRepository(ITraCuuSanPham):
    _SELECT = """SELECT sp.*, dm.ten_dm AS dm_ten, dm.mo_ta AS dm_mo_ta,
                        dm.trang_thai AS dm_trang_thai
                 FROM san_pham sp JOIN danh_muc dm ON dm.ma_dm = sp.ma_dm"""

    def __init__(self, ket_noi_db, danh_muc_repo):
        self.ket_noi_db = ket_noi_db
        self.danh_muc_repo = danh_muc_repo

    def tim_theo_ma(self, ma_sp: str) -> SanPham:
        row = self.ket_noi_db.execute(self._SELECT + " WHERE sp.ma_sp = ?", (ma_sp,)).fetchone()
        if row is None:
            raise KhongTimThayError(f"Không tìm thấy sản phẩm {ma_sp}.", "ma_sp")
        return self._tao(row)

    def tim_tat_ca(self) -> list[SanPham]:
        return [self._tao(row) for row in self.ket_noi_db.execute(self._SELECT + " ORDER BY sp.ma_sp")]

    def tim_nhieu(self, ma_san_pham) -> dict[str, SanPham]:
        """Nạp theo lượt, không giữ cache qua các giao dịch."""
        cac_ma = sorted(set(ma_san_pham))
        ket_qua = {}
        for i in range(0, len(cac_ma), 400):
            nhom = cac_ma[i:i + 400]
            dau = ",".join("?" for _ in nhom)
            rows = self.ket_noi_db.execute(self._SELECT + f" WHERE sp.ma_sp IN ({dau})", nhom)
            ket_qua.update((row["ma_sp"], self._tao(row)) for row in rows)
        return ket_qua

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
            "danh_muc": DanhMuc(row["ma_dm"], row["dm_ten"], row["dm_mo_ta"], TrangThaiDanhMuc(row["dm_trang_thai"])),
        })
