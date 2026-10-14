"""Reset có xác nhận. Dừng server trước khi chạy: python -m scripts.reset_data."""
from app.config import Settings
from scripts.seed_data import main as seed_main

def main():
    s = Settings.from_env()
    print('Sẽ xóa số dư, giao dịch, phiên và audit của DB demo:', s.database_path)
    if input('Đã dừng server? Gõ RESET để tiếp tục: ') != 'RESET':
        print('Đã hủy.')
        return
    for suffix in ('', '-wal', '-shm'):
        s.database_path.with_name(s.database_path.name+suffix).unlink(missing_ok=True)
    seed_main()

if __name__ == '__main__':
    main()
