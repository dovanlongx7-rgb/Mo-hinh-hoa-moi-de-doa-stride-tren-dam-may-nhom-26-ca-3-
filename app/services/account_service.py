"""Quyền sở hữu được kiểm tra trước số dư và lịch sử."""
from app.db.connection import connect
from app.repositories import account_repository, transfer_repository
from app.security.permissions import ensure_owner

def list_accounts(settings, user):
    with connect(settings.database_path) as db:
        return account_repository.list_owned(db, user['id'])

def get_account(settings, user, account_id):
    with connect(settings.database_path) as db:
        account = account_repository.find(db, account_id)
        ensure_owner(account, user['id'])
        return account

def get_history(settings, user, account_id):
    with connect(settings.database_path) as db:
        ensure_owner(account_repository.find(db, account_id), user['id'])
        return transfer_repository.history(db, account_id)
