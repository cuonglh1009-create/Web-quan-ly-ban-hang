from dataclasses import asdict, dataclass, field

from kho_ban_hang.contracts.kho_contract import ChiTietDatHangDTO
from kho_ban_hang.contracts.kiem_tra_dau_vao import chuoi_bat_buoc, chuoi_tuy_chon, so_nguyen
from kho_ban_hang.domain.errors_ban_hang import LoiDuLieu

SO_LUONG_TOI_DA = 1_000_000   # giả định của TV2, chặn tràn số


class _DTO:
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DuLieuLapDonDTO(_DTO):
    ma_kh: str | None
    dong: list[ChiTietDatHangDTO]
    ten_kh: str | None = None
    sdt_kh: str | None = None
    dia_chi_kh: str | None = None

    @classmethod
    def tu_json(cls, d: dict) -> "DuLieuLapDonDTO":
        ma_kh = d.get("ma_kh")
        ma_kh = None if ma_kh in (None, "") else chuoi_bat_buoc(ma_kh, "ma_kh")
        ten_kh = chuoi_tuy_chon(d.get("ten_kh"), "ten_kh", 160)
        sdt_kh = chuoi_tuy_chon(d.get("sdt_kh"), "sdt_kh", 40)
        dia_chi_kh = chuoi_tuy_chon(d.get("dia_chi_kh"), "dia_chi_kh", 500)
        raw = d.get("dong")
        if not isinstance(raw, list) or not raw:
            raise LoiDuLieu("DONG_RONG", "Đơn phải có ít nhất một dòng", "dong")
        dong = []
        for i, r in enumerate(raw):          # truong dạng dong[i].ma_sp để giao diện tô đúng dòng
            if not isinstance(r, dict):
                raise LoiDuLieu("DONG_KHONG_HOP_LE", "Dòng không hợp lệ", f"dong[{i}]")
            dong.append(ChiTietDatHangDTO(
                chuoi_bat_buoc(r.get("ma_sp"), f"dong[{i}].ma_sp"),
                so_nguyen(r.get("so_luong"), f"dong[{i}].so_luong", 1, SO_LUONG_TOI_DA)))
        return cls(ma_kh, dong, ten_kh, sdt_kh, dia_chi_kh)


@dataclass
class KetQuaLapDonDTO(_DTO):
    ma_don: str
    trang_thai: str
    tam_tinh: int
    giam_hang_khach: int
    giam_khuyen_mai: int
    so_phai_tra: int
    ma_kh: str | None = None
    ten_kh: str | None = None
    hang_kh: str | None = None
    dong: list[dict] = field(default_factory=list)

    @classmethod
    def tu_don_hang(cls, don) -> "KetQuaLapDonDTO":
        ma_kh = don.khach_hang.ma_kh if don.khach_hang else None
        ten_kh = don.khach_hang.ho_ten if don.khach_hang else None
        hang_kh = "VIP" if (don.khach_hang and getattr(don.khach_hang, "la_vip", False)) else ("THUONG" if don.khach_hang else None)
        return cls(don.ma_don, don.trang_thai.value, don.tinh_tam_tinh(),
                   don.giam_hang_khach, don.giam_khuyen_mai, don.so_phai_tra(),
                   ma_kh, ten_kh, hang_kh, [
                       {"ma_sp": ct.san_pham.ma_sp, "ten_sp": ct.san_pham.ten_sp,
                        "don_vi_tinh": ct.san_pham.don_vi_tinh, "so_luong": ct.so_luong,
                        "don_gia": ct.don_gia, "thanh_tien": ct.thanh_tien()}
                       for ct in don.chi_tiet
                   ])


@dataclass
class KetQuaThanhToanDTO(_DTO):
    ma_hd: str
    so_phai_tra: int
    tien_thoi: int | None
    da_hoan_tat_truoc_do: bool


@dataclass
class KetQuaHuyDonDTO(_DTO):
    ma_don: str
    trang_thai: str


@dataclass
class HoaDonDTO(_DTO):
    ma_hd: str
    ma_don: str
    ngay_xuat: str
    tong_tien_truoc_giam: int
    tong_giam: int
    tong_thanh_toan: int
    phuong_thuc: str
    tien_thoi: int | None
    dong: list[dict] = field(default_factory=list)   # ma_sp, so_luong, don_gia, thanh_tien
