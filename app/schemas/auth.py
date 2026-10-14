"""Mẫu input chặt chẽ; không cho field thừa hoặc mật khẩu dài vô hạn."""
from pydantic import BaseModel, ConfigDict, Field

class LoginInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=1, max_length=50, pattern=r"^[a-z0-9_]+$")
    password: str = Field(min_length=1, max_length=128)
