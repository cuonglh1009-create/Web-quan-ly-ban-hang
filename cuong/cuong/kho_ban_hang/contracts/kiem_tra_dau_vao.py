from kho_ban_hang.domain.errors_ban_hang import LoiDuLieu


def chuoi_bat_buoc(v, truong: str, toi_da: int = 100) -> str:
    if not isinstance(v, str) or not v.strip():
        raise LoiDuLieu("TRUONG_BAT_BUOC", "Trường này là bắt buộc", truong)
    v = v.strip()
    if len(v) > toi_da:
        raise LoiDuLieu("TRUONG_QUA_DAI", f"Tối đa {toi_da} ký tự", truong)
    return v


def so_nguyen(v, truong: str, toi_thieu: int = 0, toi_da: int = 10**12) -> int:
    if isinstance(v, bool) or not isinstance(v, int) or not (toi_thieu <= v <= toi_da):
        raise LoiDuLieu("SO_KHONG_HOP_LE",
                        f"Cần số nguyên trong khoảng {toi_thieu}..{toi_da}", truong)
    return v
