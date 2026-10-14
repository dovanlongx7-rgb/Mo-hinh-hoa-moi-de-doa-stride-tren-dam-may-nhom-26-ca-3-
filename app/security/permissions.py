"""Kiểm tra danh tính tại server; không lấy user_id do client khai báo."""
import time
import jwt
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.db.connection import connect
from app.security.tokens import decode_token
from app.repositories.user_repository import find_id

bearer = HTTPBearer(auto_error=False)

def deny(status, code):
    raise HTTPException(status_code=status, detail=code)

def current_user(request: Request, credential: HTTPAuthorizationCredentials | None = Depends(bearer)):
    if credential is None or credential.scheme.lower() != "bearer":
        deny(401, "AUTH_REQUIRED")
    try:
        payload = decode_token(credential.credentials, request.app.state.jwt_secret)
    except jwt.PyJWTError:
        deny(401, "INVALID_SESSION")
    with connect(request.app.state.settings.database_path) as db:
        session = db.execute("SELECT * FROM sessions WHERE id=? AND user_id=?", (payload['jti'], payload['sub'])).fetchone()
        user = find_id(db, payload['sub'])
    if not session or session['revoked'] or session['expires_at'] <= int(time.time()) or not user:
        deny(401, "INVALID_SESSION")
    request.state.principal = user['id']
    user['session_id'] = payload['jti']
    return user

def ensure_owner(account, user_id):
    # Cùng lỗi cho không tồn tại và thuộc người khác: không lộ tài nguyên.
    if not account or account['user_id'] != user_id:
        deny(403, "ACCOUNT_ACCESS_DENIED")

def operator_only(user):
    if user['role'] != "operator":
        deny(403, "ROLE_DENIED")
