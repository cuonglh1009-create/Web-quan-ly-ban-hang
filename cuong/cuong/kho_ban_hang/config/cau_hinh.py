"""CauHinh dùng chung TV1/TV2. Tên khóa đổi thì hai bên cùng duyệt."""
import os
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class CauHinh:
    duong_dan_csdl: str = "kho_ban_hang.db"
    nguong_ton_kho: int = 5
    so_ngay_canh_bao: int = 30
    so_tien_moi_diem: int = 10_000          # bao nhiêu đồng thực trả = 1 điểm
    nguong_diem_vip: int = 1000             # đủ điểm này thì nâng VIP
    thoi_han_phien_gio: int = 8
    ty_le_chiet_khau_thuong: Decimal = Decimal("0")
    ty_le_chiet_khau_vip: Decimal = Decimal("0.05")
    # --- khóa bổ sung do TV2 thêm (cần TV1 duyệt) ---
    khoa_bi_mat: str = ""                   # đọc từ môi trường, dùng băm mã phiên
    cookie_secure: bool = False
    so_lan_thu_toi_da: int = 5
    cua_so_thu_giay: int = 900
    dung_kho_gia: bool = False              # True: dùng KhoGia khi Kho của TV1 chưa xong

    @classmethod
    def tu_moi_truong(cls) -> "CauHinh":
        khoa = os.environ.get("KBH_KHOA_BI_MAT", "")
        if len(khoa) < 16:
            raise RuntimeError(
                "Thiếu biến môi trường KBH_KHOA_BI_MAT (tối thiểu 16 ký tự)."
            )
        return cls(
            duong_dan_csdl=os.environ.get("KBH_CSDL", cls.duong_dan_csdl),
            khoa_bi_mat=khoa,
            cookie_secure=os.environ.get("KBH_COOKIE_SECURE") == "1",
            dung_kho_gia=os.environ.get("KBH_DUNG_KHO_GIA") == "1",
        )
