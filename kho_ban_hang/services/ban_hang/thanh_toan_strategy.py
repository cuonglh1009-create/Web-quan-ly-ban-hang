from datetime import datetime

from kho_ban_hang.contracts.thanh_toan_contract import IPhuongThucThanhToan, ThongTinThanhToanDTO
from kho_ban_hang.domain.errors_ban_hang import LoiDuLieu
from kho_ban_hang.domain.thanh_toan import (ThanhToan, ThanhToanChuyenKhoan,
                                            ThanhToanTienMat, moi_ma_gd)


class ThanhToanTienMatStrategy(IPhuongThucThanhToan):
    def xu_ly(self, don_hang, thong_tin: ThongTinThanhToanDTO) -> ThanhToan:
        phai_tra = don_hang.so_phai_tra()          # số đã chốt từ đơn, không tin client
        dua = thong_tin.tien_khach_dua or 0
        if dua < phai_tra:
            raise LoiDuLieu("TIEN_THIEU", f"Khách đưa thiếu {phai_tra - dua} đồng",
                            "thong_tin.tien_khach_dua")
        return ThanhToanTienMat(moi_ma_gd(), don_hang, phai_tra, datetime.now(),
                                tien_khach_dua=dua, tien_thoi=dua - phai_tra)


class ThanhToanChuyenKhoanStrategy(IPhuongThucThanhToan):
    def xu_ly(self, don_hang, thong_tin: ThongTinThanhToanDTO) -> ThanhToan:
        phai_tra = don_hang.so_phai_tra()
        if thong_tin.so_tien_doi_soat != phai_tra:
            raise LoiDuLieu("SO_TIEN_KHONG_KHOP",
                            f"Số tiền đối soát phải bằng số phải trả ({phai_tra})",
                            "thong_tin.so_tien_doi_soat")
        return ThanhToanChuyenKhoan(moi_ma_gd(), don_hang, phai_tra, datetime.now(),
                                    ma_giao_dich_ngan_hang=thong_tin.ma_giao_dich_ngan_hang,
                                    ten_ngan_hang=thong_tin.ten_ngan_hang)
