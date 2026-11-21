"""Contract phân trang tùy chọn; lời gọi cũ vẫn nhận danh sách."""
from math import ceil
from ..domain.errors import DuLieuKhongHopLeError


def doc_phan_trang(args):
    if "page" not in args and "page_size" not in args:
        return None, 20
    try:
        page = int(args.get("page", 1))
        size = int(args.get("page_size", 20))
        if page < 1 or not 1 <= size <= 100:
            raise ValueError
    except (TypeError, ValueError):
        raise DuLieuKhongHopLeError("Trang phải từ 1; số dòng mỗi trang từ 1 đến 100.", "page")
    return page, size


def lay_trang(db, sql, params=(), page=1, page_size=20):
    if type(page) is not int or page < 1 or type(page_size) is not int or not 1 <= page_size <= 100:
        raise DuLieuKhongHopLeError("Thông tin phân trang không hợp lệ.", "page")
    # SQL là câu đọc cố định do repository xây dựng, không nhận SQL từ người dùng.
    count_sql = sql.rsplit("ORDER BY", 1)[0] if "ORDER BY" in sql else sql
    with_snapshot = not db.in_transaction
    if with_snapshot:
        db.execute("BEGIN")
    try:
        total = db.execute("SELECT COUNT(*) FROM (" + count_sql + ") AS ds", params).fetchone()[0]
        pages = max(1, ceil(total / page_size))
        page = min(page, pages)
        rows = db.execute(sql + " LIMIT ? OFFSET ?", [*params, page_size, (page-1)*page_size]).fetchall()
        return {"items": [dict(row) for row in rows], "total": total, "page": page,
                "page_size": page_size, "pages": pages}
    finally:
        if with_snapshot:
            db.rollback()  # Kết thúc snapshot chỉ đọc, không tác động giao dịch của caller.
