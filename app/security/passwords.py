"""Băm mật khẩu Argon2id; muối được thư viện tự sinh."""
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError

hasher = PasswordHasher()
# Băm giả để tránh nhánh tài khoản không tồn tại bỏ qua phép kiểm tra mật khẩu.
dummy_hash = hasher.hash("not-a-real-user-password")

def hash_password(password: str) -> str:
    return hasher.hash(password)

def verify_password(encoded: str, password: str) -> bool:
    try:
        return hasher.verify(encoded, password)
    except (VerificationError, InvalidHashError):
        return False
