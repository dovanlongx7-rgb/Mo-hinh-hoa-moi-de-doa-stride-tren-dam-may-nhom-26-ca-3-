from dataclasses import replace
import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from scripts.seed_data import seed

PASSWORD = 'Testing-only-password-2026'

@pytest.fixture
def bank(tmp_path):
    settings = replace(Settings(), database_path=tmp_path/'bank.sqlite3', key_path=tmp_path/'key',
                       login_requests=1000, transfer_requests=1000)
    app = create_app(settings)
    with TestClient(app, raise_server_exceptions=False) as client:
        seed(settings.database_path, PASSWORD)
        yield client, app, settings
