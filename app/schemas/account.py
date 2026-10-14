"""Dữ liệu tài khoản trả về; không chứa mật khẩu hoặc khóa."""
from pydantic import BaseModel

class AccountOutput(BaseModel):
    id: str
    user_id: str
    balance: int
