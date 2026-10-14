"""API xác thực, phiên và quyền vận hành."""
from fastapi import APIRouter, Request, Depends
from app.schemas.auth import LoginInput
from app.security.permissions import current_user, operator_only
from app.repositories.user_repository import public_user
from app.services import auth_service, audit_service

router = APIRouter(prefix="/api", tags=["Xác thực"])

@router.post("/auth/login")
def login(payload: LoginInput, request: Request):
    s = request.app.state.settings
    ip = request.client.host if request.client else "unknown"
    request.app.state.limiter.check(('login', ip), s.login_requests, s.window_seconds)
    result = auth_service.login(s, request.app.state.jwt_secret, payload.username, payload.password)
    request.state.principal = result['user']['id']
    return result

@router.get("/auth/me")
def me(user=Depends(current_user)):
    return public_user(user)

@router.post("/auth/logout")
def logout(request: Request, user=Depends(current_user)):
    auth_service.logout(request.app.state.settings, user['session_id'])
    return {"message": "Đã đăng xuất."}

@router.get("/admin/audit")
def audit(request: Request, user=Depends(current_user)):
    operator_only(user)
    return audit_service.list_events(request.app.state.settings.database_path)
