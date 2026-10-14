"""Kết nối mới cho mỗi thao tác; giao dịch ghi được khóa bằng BEGIN IMMEDIATE."""
from contextlib import contextmanager
from pathlib import Path
import sqlite3
from app.db.models import SCHEMA

@contextmanager
def connect(path: Path):
    db = sqlite3.connect(str(path), timeout=10, isolation_level=None)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA busy_timeout=10000")
    try:
        yield db
    finally:
        db.close()

@contextmanager
def transaction(path: Path):
    with connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise

def initialize(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.executescript(SCHEMA)
