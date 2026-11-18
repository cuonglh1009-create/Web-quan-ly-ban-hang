from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

from ..domain.enums_kho import LoaiCanhBao


@dataclass(frozen=True)
class ChiTietDatHangDTO:
    ma_sp: str
    so_luong: int


@dataclass(frozen=True)
class CanhBaoDTO:
    loai: LoaiCanhBao
    noi_dung: str
    ma_sp: str | None = None
    ma_lo: str | None = None
    so_kha_dung: int | None = None
    han_su_dung: date | None = None


class IKho(ABC):
    @abstractmethod
    def lay_so_luong_kha_dung(self, ma_sp: str) -> int: ...

    @abstractmethod
    def giu_hang(self, ma_don: str, chi_tiet: list[ChiTietDatHangDTO]) -> None: ...

    @abstractmethod
    def xac_nhan_xuat_kho(self, ma_don: str) -> None: ...

    @abstractmethod
    def hoan_giu_hang(self, ma_don: str) -> None: ...


class IKhoObserver(ABC):
    @abstractmethod
    def cap_nhat(self, canh_bao: CanhBaoDTO) -> None: ...
