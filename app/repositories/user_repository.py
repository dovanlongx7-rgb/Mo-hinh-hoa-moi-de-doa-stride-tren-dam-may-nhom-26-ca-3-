"""Truy vấn tham số cho người dùng; không trả password_hash qua API."""
def find_username(db, username):
    row = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    return dict(row) if row else None

def find_id(db, user_id):
    row = db.execute("SELECT id,username,full_name,role FROM users WHERE id=?", (user_id,)).fetchone()
    return dict(row) if row else None

def public_user(user):
    return {k: user[k] for k in ("id", "username", "full_name", "role")}
