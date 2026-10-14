"""Đọc lịch sử và kết quả idempotency; giao dịch ghi do service điều phối."""
def find(db, transfer_id):
    row = db.execute("SELECT * FROM transfers WHERE id=?", (transfer_id,)).fetchone()
    return dict(row) if row else None

def previous(db, user_id, key):
    row = db.execute("SELECT * FROM idempotency WHERE user_id=? AND endpoint='transfer' AND key=?", (user_id, key)).fetchone()
    return dict(row) if row else None

def history(db, account_id):
    return [dict(r) for r in db.execute(
        "SELECT * FROM transfers WHERE source_account_id=? OR target_account_id=? ORDER BY created_at DESC LIMIT 100",
        (account_id, account_id))]

def total_today(db, user_id, day):
    return db.execute("SELECT COALESCE(SUM(amount),0) FROM transfers WHERE user_id=? AND day_utc=?", (user_id, day)).fetchone()[0]
