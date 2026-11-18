from dataclasses import dataclass
from typing import Any


@dataclass
class PhanHoi:
    """Kết quả controller; lớp web đổi thành HTTP response."""
    du_lieu: Any
    status: int = 200
    dat_cookie: str | None = None     # mã phiên ngẫu nhiên cần đặt vào cookie
    xoa_cookie: bool = False
