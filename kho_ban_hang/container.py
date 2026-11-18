"""Container tạo theo từng yêu cầu: một kết nối SQLite, đóng khi yêu cầu kết thúc."""
import sqlite3
from functools import cached_property

from kho_ban_hang.controllers.ban_hang_controller import BanHangController
from kho_ban_hang.controllers.kho_controller import KhoController
from kho_ban_hang.controllers.xac_thuc_controller import XacThucController
from kho_ban_hang.domain.enums_chung import PhuongThucThanhToan
from kho_ban_hang.repositories.ban_hang.don_hang_repository import DonHangRepository
from kho_ban_hang.repositories.ban_hang.hoa_don_repository import HoaDonRepository
from kho_ban_hang.repositories.ban_hang.khach_hang_repository import KhachHangRepository
from kho_ban_hang.repositories.ban_hang.khuyen_mai_repository import KhuyenMaiRepository
from kho_ban_hang.repositories.ban_hang.nhan_vien_repository import NhanVienRepository
from kho_ban_hang.repositories.ban_hang.phien_lam_viec_repository import PhienLamViecRepository
from kho_ban_hang.repositories.ban_hang.thanh_toan_repository import ThanhToanRepository
from kho_ban_hang.repositories.giao_dich import ket_noi
from kho_ban_hang.services.ban_hang.ban_hang_service import BanHangService
from kho_ban_hang.services.ban_hang.thanh_toan_service import ThanhToanService
from kho_ban_hang.services.ban_hang.thanh_toan_strategy import (ThanhToanChuyenKhoanStrategy,
                                                                 ThanhToanTienMatStrategy)
from kho_ban_hang.services.ban_hang.xac_thuc_service import XacThucService
from kho_ban_hang.services.kho.dang_ky import dang_ky_kho


def mo_ket_noi(duong_dan: str) -> sqlite3.Connection:
    db = ket_noi(duong_dan)
    db.execute("PRAGMA journal_mode = WAL")
    return db


class Container:
    def __init__(self, cau_hinh, bo_dem_thu, kho_gia=None, tra_cuu_gia=None, dong_ho=None):
        self.cau_hinh, self.bo_dem_thu, self.dong_ho = cau_hinh, bo_dem_thu, dong_ho
        self._kho_gia, self._tra_cuu_gia = kho_gia, tra_cuu_gia

    @cached_property
    def ket_noi(self):
        return mo_ket_noi(self.cau_hinh.duong_dan_csdl)

    def dong(self):
        if "ket_noi" in self.__dict__:
            self.ket_noi.close()

    @cached_property
    def thanh_phan_kho(self):
        return dang_ky_kho(self.ket_noi, self.cau_hinh, self.nhan_vien_repo.tim_theo_ma)

    @cached_property
    def kho(self):
        return self._kho_gia if self.cau_hinh.dung_kho_gia else self.thanh_phan_kho.kho

    @cached_property
    def tra_cuu_san_pham(self):
        return self._tra_cuu_gia if self.cau_hinh.dung_kho_gia else self.thanh_phan_kho.san_pham_repo

    @cached_property
    def kho_controller(self): return KhoController(self.xac_thuc, self.thanh_phan_kho)

    # repository
    @cached_property
    def nhan_vien_repo(self): return NhanVienRepository(self.ket_noi)
    @cached_property
    def phien_repo(self): return PhienLamViecRepository(self.ket_noi)
    @cached_property
    def khach_repo(self): return KhachHangRepository(self.ket_noi)
    @cached_property
    def km_repo(self): return KhuyenMaiRepository(self.ket_noi)

    @cached_property
    def don_repo(self):
        return DonHangRepository(self.ket_noi, self.nhan_vien_repo, self.khach_repo,
                                 self.km_repo, self.tra_cuu_san_pham)

    @cached_property
    def thanh_toan_repo(self): return ThanhToanRepository(self.ket_noi, self.don_repo)
    @cached_property
    def hoa_don_repo(self): return HoaDonRepository(self.ket_noi, self.don_repo, self.thanh_toan_repo)

    #  service / controller
    @cached_property
    def xac_thuc(self):
        return XacThucService(self.nhan_vien_repo, self.phien_repo, self.cau_hinh,
                              self.bo_dem_thu, self.dong_ho)

    @cached_property
    def ban_hang(self):
        return BanHangService(self.kho, self.tra_cuu_san_pham, self.don_repo, self.khach_repo,
                              self.km_repo, self.ket_noi, self.cau_hinh)

    @cached_property
    def thanh_toan_service(self):
        return ThanhToanService(
            self.kho, self.don_repo, self.khach_repo, self.thanh_toan_repo, self.hoa_don_repo,
            self.ket_noi,
            {PhuongThucThanhToan.TIEN_MAT: ThanhToanTienMatStrategy(),
             PhuongThucThanhToan.CHUYEN_KHOAN: ThanhToanChuyenKhoanStrategy()},
            self.cau_hinh)

    @cached_property
    def xac_thuc_controller(self): return XacThucController(self.xac_thuc)

    @cached_property
    def ban_hang_controller(self):
        return BanHangController(self.xac_thuc, self.ban_hang, self.thanh_toan_service)
