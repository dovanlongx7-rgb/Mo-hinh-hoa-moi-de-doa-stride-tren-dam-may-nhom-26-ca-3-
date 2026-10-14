"""Phiên được lưu server để đăng xuất có hiệu lực ngay."""
import secrets
import time
from app.db.connection import transaction
from app.repositories.user_repository import find_username, public_user
from app.security.passwords import verify_password, dummy_hash
from app.security.tokens import issue_token
from app.security.permissions import deny

def login(settings, secret, username, password):
    with transaction(settings.database_path) as db:
        user = find_username(db, username)
        valid = verify_password(user['password_hash'] if user else dummy_hash, password)
        if not valid or user is None:
            deny(401, "INVALID_CREDENTIALS")
        session_id = secrets.token_urlsafe(24)
        db.execute("INSERT INTO sessions(id,user_id,expires_at) VALUES(?,?,?)",
                   (session_id, user['id'], int(time.time())+settings.token_seconds))
    token = issue_token(user['id'], session_id, secret, settings.token_seconds)
    return {"access_token": token, "token_type": "bearer", "expires_in": settings.token_seconds,
            "user": public_user(user)}

def logout(settings, session_id):
    with transaction(settings.database_path) as db:
        db.execute("UPDATE sessions SET revoked=1 WHERE id=?", (session_id,))
