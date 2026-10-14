"""API chuyển tiền và xác thực lại, với giới hạn độc lập theo danh tính."""
from uuid import UUID
from fastapi import APIRouter, Request, Depends, Header
from fastapi.responses import JSONResponse
from app.schemas.transfer import ReauthInput, TransferInput
from app.security.permissions import current_user, deny
from app.services import transfer_service

router = APIRouter(prefix="/api/transfers", tags=["Chuyển tiền"])

@router.post("/reauth")
def reauth(payload: ReauthInput, request: Request, user=Depends(current_user)):
    s = request.app.state.settings
    request.app.state.limiter.check(('reauth', user['id']), s.login_requests, s.window_seconds)
    return transfer_service.create_proof(s, user, payload)

@router.post("")
def transfer(payload: TransferInput, request: Request, user=Depends(current_user),
             idempotency_key: str = Header(min_length=8, max_length=128, alias="Idempotency-Key")):
    try:
        key = str(UUID(idempotency_key))
    except (ValueError, AttributeError):
        deny(422, "INVALID_IDEMPOTENCY_KEY")
    s = request.app.state.settings
    request.app.state.limiter.check(('transfer', user['id']), s.transfer_requests, s.window_seconds)
    result, replayed = transfer_service.execute(s, user, payload, key, request.state.trace_id)
    return JSONResponse({"transaction": result, "replayed": replayed}, status_code=200 if replayed else 201)
