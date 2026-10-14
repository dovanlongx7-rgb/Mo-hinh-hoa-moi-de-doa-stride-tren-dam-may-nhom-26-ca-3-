"""Cấu hình cho nguyên mẫu local; đường dẫn được tính từ thư mục repo."""
from dataclasses import dataclass
from pathlib import Path
import os
import secrets
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]

@dataclass(frozen=True)
class Settings:
    database_path: Path = ROOT / "runtime/bank.sqlite3"
    key_path: Path = ROOT / "runtime/jwt.key"
    token_seconds: int = 1800
    proof_seconds: int = 180
    per_transfer_limit: int = 300_000
    daily_limit: int = 600_000
    transfer_requests: int = 10
    window_seconds: int = 60
    login_requests: int = 5
    max_body_bytes: int = 16_384

    @classmethod
    def from_env(cls):
        load_dotenv(ROOT / ".env", override=False)
        def path(name, default):
            p = Path(os.environ.get(name, str(default)))
            return p if p.is_absolute() else ROOT / p
        return cls(database_path=path("BANK_DATABASE_PATH", ROOT / "runtime/bank.sqlite3"),
                   key_path=path("BANK_KEY_PATH", ROOT / "runtime/jwt.key"))

def load_or_create_key(path: Path) -> str:
    """Tạo khóa riêng cho máy chạy; giữ nguyên qua restart; không đóng gói khóa."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        pass
    else:
        with os.fdopen(fd, "w", encoding="ascii") as f:
            f.write(secrets.token_urlsafe(48))
    key = path.read_text(encoding="ascii").strip()
    if len(key) < 48:
        raise RuntimeError("Khóa local không hợp lệ; cần ít nhất 48 ký tự ngẫu nhiên.")
    return key
