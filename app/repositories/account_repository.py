"""Các câu SQL cho tài khoản đều dùng tham số."""
def find(db, account_id):
    row = db.execute("SELECT * FROM accounts WHERE id=?", (account_id,)).fetchone()
    return dict(row) if row else None

def list_owned(db, user_id):
    return [dict(r) for r in db.execute("SELECT * FROM accounts WHERE user_id=? ORDER BY id", (user_id,))]
