"""Kiểm tra DB đã tồn tại, không seed/reset và không in thông tin xác thực.
Chạy tại repo: python -m scripts.inspect_database
"""
import argparse
import json
from pathlib import Path
from app.config import Settings
from app.db.connection import connect

TABLES = ('users','accounts','sessions','reauth_proofs','transfers','idempotency','audit_events')

def inspect_database(path: Path):
    if not path.is_file():
        raise RuntimeError('Chưa có database. Chạy python -m scripts.seed_data trước.')
    with connect(path) as db:
        existing = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        missing = set(TABLES)-existing
        if missing:
            raise RuntimeError('Thiếu bảng: '+', '.join(sorted(missing)))
        # Tên bảng lấy từ hằng TABLES; không nội suy dữ liệu người dùng vào SQL.
        counts = {table: db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0] for table in TABLES}
        accounts = [dict(r) for r in db.execute('''
            SELECT u.id AS user_id,u.username,u.full_name,a.id AS account_id,a.balance
            FROM users u JOIN accounts a ON a.user_id=u.id ORDER BY a.id
        ''')]
        hashes = [r[0] for r in db.execute('SELECT password_hash FROM users')]
        integrity_ok = db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        foreign_key_violations = len(db.execute('PRAGMA foreign_key_check').fetchall())
    return {'database_path':str(path.resolve()),'table_counts':counts,'accounts':accounts,
            'passwords_argon2id':bool(hashes) and all(h.startswith('$argon2id$') for h in hashes),
            'integrity_ok':integrity_ok,'foreign_key_violations':foreign_key_violations}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database',type=Path,help='Đường dẫn DB khác, nếu cần')
    args=parser.parse_args()
    try:
        result=inspect_database(args.database or Settings.from_env().database_path)
    except RuntimeError as exc:
        print(exc)
        raise SystemExit(1) from None
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if not result['integrity_ok'] or result['foreign_key_violations'] or not result['passwords_argon2id']:
        raise SystemExit(1)

if __name__=='__main__':
    main()
