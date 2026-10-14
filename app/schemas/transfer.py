"""Số tiền phải là số nguyên dương, không chấp nhận boolean hoặc số thực."""
from pydantic import BaseModel, ConfigDict, Field

class TransferIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_account_id: str = Field(min_length=1, max_length=50)
    target_account_id: str = Field(min_length=1, max_length=50)
    amount: int = Field(strict=True, gt=0, le=10**12)

class ReauthInput(TransferIntent):
    password: str = Field(min_length=1, max_length=128)

class TransferInput(TransferIntent):
    reauth_proof: str | None = Field(default=None, max_length=256)
