"""API tài khoản chỉ trả dữ liệu sau khi kiểm tra chủ sở hữu."""
from fastapi import APIRouter, Request, Depends
from app.security.permissions import current_user
from app.schemas.account import AccountOutput
from app.services import account_service

router = APIRouter(prefix="/api/accounts", tags=["Tài khoản"])

@router.get("", response_model=list[AccountOutput])
def accounts(request: Request, user=Depends(current_user)):
    return account_service.list_accounts(request.app.state.settings, user)

@router.get("/{account_id}", response_model=AccountOutput)
def account(account_id: str, request: Request, user=Depends(current_user)):
    return account_service.get_account(request.app.state.settings, user, account_id)

@router.get("/{account_id}/history")
def history(account_id: str, request: Request, user=Depends(current_user)):
    return account_service.get_history(request.app.state.settings, user, account_id)
