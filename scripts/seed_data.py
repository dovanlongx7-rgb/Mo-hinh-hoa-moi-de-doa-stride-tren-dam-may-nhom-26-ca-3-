"""Tạo tài khoản mẫu. Chạy từ repo: python -m scripts.seed_data."""
import getpass
import json
import os
from app.config import Settings, ROOT
from app.db.connection import initialize, transaction
from app.security.passwords import hash_password

def seed(path, password):
    if len(password) < 10:
        raise ValueError('Mật khẩu mẫu cần ít nhất 10 ký tự.')
    initialize(path)
    records = json.loads((ROOT / 'data/sample_accounts.json').read_text(encoding='utf-8'))
    with transaction(path) as db:
        if db.execute('SELECT COUNT(*) FROM users').fetchone()[0]:
            raise RuntimeError('DB đã có dữ liệu. Không seed đè; dùng reset có xác nhận nếu cần.')
        for record in records:
            db.execute('INSERT INTO users(id,username,full_name,password_hash) VALUES(?,?,?,?)',
                       (record['user_id'],record['username'],record['full_name'],hash_password(password)))
            db.execute('INSERT INTO accounts(id,user_id,balance) VALUES(?,?,?)',
                       (record['account_id'],record['user_id'],record['balance']))

def main():
    password = os.environ.get('BANK_DEMO_PASSWORD') or getpass.getpass('Nhập mật khẩu mẫu dùng chung (ít nhất 10 ký tự): ')
    seed(Settings.from_env().database_path, password)
    print('Đã tạo van_a / van_b / van_c. Không có tiền thật.')

if __name__ == '__main__':
    main()
