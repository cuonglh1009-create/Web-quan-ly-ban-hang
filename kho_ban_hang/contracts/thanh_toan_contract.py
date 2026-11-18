from abc import ABC, abstractmethod
from dataclasses import dataclass

from kho_ban_hang.contracts.kiem_tra_dau_vao import chuoi_bat_buoc, so_nguyen
from kho_ban_hang.domain.don_hang import DonHang
from kho_ban_hang.domain.enums_chung import PhuongThucThanhToan
from kho_ban_hang.domain.errors_ban_hang import LoiDuLieu
from kho_ban_hang.domain.thanh_toan import ThanhToan


@dataclass
class ThongTinThanhToanDTO:
    phuong_thuc: PhuongThucThanhToan
    tien_khach_dua: int | None = None
    so_tien_doi_soat: int | None = None
    ten_ngan_hang: str | None = None
    ma_giao_dich_ngan_hang: str | None = None

    @classmethod
    def tu_json(cls, phuong_thuc, thong_tin) -> "ThongTinThanhToanDTO":
        try:
            pt = PhuongThucThanhToan(phuong_thuc)
        except ValueError:
            raise LoiDuLieu("PHUONG_THUC_KHONG_HOP_LE",
                            "phuong_thuc phải là TIEN_MAT hoặc CHUYEN_KHOAN", "phuong_thuc")
        tt = thong_tin if isinstance(thong_tin, dict) else {}
        if pt == PhuongThucThanhToan.TIEN_MAT:
            return cls(pt, tien_khach_dua=so_nguyen(tt.get("tien_khach_dua"),
                                                   "thong_tin.tien_khach_dua"))
        return cls(pt,
                   so_tien_doi_soat=so_nguyen(tt.get("so_tien_doi_soat"),
                                              "thong_tin.so_tien_doi_soat"),
                   ten_ngan_hang=chuoi_bat_buoc(tt.get("ten_ngan_hang"), "thong_tin.ten_ngan_hang"),
                   ma_giao_dich_ngan_hang=chuoi_bat_buoc(tt.get("ma_giao_dich_ngan_hang"),
                                                         "thong_tin.ma_giao_dich_ngan_hang"))


class IPhuongThucThanhToan(ABC):
    """Strategy. Chỉ tính và trả kết quả; service mới là nơi lưu trong giao dịch."""

    @abstractmethod
    def xu_ly(self, don_hang: DonHang, thong_tin: ThongTinThanhToanDTO) -> ThanhToan: ...
