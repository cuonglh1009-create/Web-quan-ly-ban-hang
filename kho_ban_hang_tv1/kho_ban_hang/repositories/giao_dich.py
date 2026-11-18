import sqlite3


def ket_noi(duong_dan: str) -> sqlite3.Connection:
    conn = sqlite3.connect(duong_dan, timeout=5, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


class GiaoDich:
    def __init__(self, ket_noi_db: sqlite3.Connection):
        self.ket_noi_db = ket_noi_db

    def __enter__(self):
        self.ket_noi_db.execute("BEGIN IMMEDIATE")
        return self.ket_noi_db

    def __exit__(self, loai_loi, loi, vet_loi):
        try:
            if loai_loi is None:
                self.ket_noi_db.commit()
            else:
                self.ket_noi_db.rollback()
        except Exception:
            self.ket_noi_db.rollback()
            raise
