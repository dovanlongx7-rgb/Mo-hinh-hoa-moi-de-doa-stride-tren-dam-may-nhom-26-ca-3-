# Backend giai đoạn 3 — API và xử lý nghiệp vụ

Gói này nối frontend giai đoạn 1 với database giai đoạn 2. Ứng dụng là nguyên mẫu FastAPI + SQLite chạy local, dùng dữ liệu ngân hàng giả lập.

## Ghép file và chạy

Giải nén, copy nội dung thư mục `stride-banking` vào đúng thư mục repo chứa `app/`, `scripts/`, `data/`. Cần có file của cả ba giai đoạn trong cùng thư mục. Các file dùng chung là cùng bộ code; nếu đã sửa trên máy, đối chiếu trước khi ghi đè. Không xóa database đã tạo.

Mở Terminal PowerShell tại thư mục repo:

```powershell
# Chỉ chạy lệnh này nếu chưa có .venv:
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
# Chỉ seed nếu chưa tạo dữ liệu ở giai đoạn 2:
.\.venv\Scripts\python.exe -m scripts.seed_data
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Nếu database đã có người dùng thì bỏ lệnh seed. Seed không ghi đè dữ liệu hiện có. Mật khẩu đăng nhập là mật khẩu bạn đặt khi seed, không mặc định là mật khẩu bản frontend demo.

- App: http://127.0.0.1:8000/ — giao diện gọi API và lưu giao dịch vào SQLite.
- Trạng thái: http://127.0.0.1:8000/health
- Tài liệu API tương tác: http://127.0.0.1:8000/api-docs (Swagger tải tài nguyên ngoài, cần mạng để hiển thị).
- Cổng 5500 của `preview_frontend` vẫn là dữ liệu giả trong trình duyệt; không dùng để kiểm tra backend.

## Thử luồng đầu tiên

1. Đăng nhập `van_a`, xem ACC_A. Với dữ liệu seed mới, số dư là 1.000.000 VND.
2. Chuyển 100.000 VND sang ACC_B, nhập lại mật khẩu và xác nhận.
3. Xem lịch sử: có một giao dịch; ACC_A còn 900.000 VND.
4. Đăng xuất, đăng nhập `van_b`: ACC_B có 600.000 VND.

Nếu đã có giao dịch từ trước, tính số dư dựa trên số dư hiện có. Không reset chỉ để khớp số liệu ví dụ. Đóng/mở backend vẫn giữ dữ liệu database.

## Đọc code theo thứ tự

`app/main.py` → `app/routers/` → `app/schemas/` → `app/security/` → `app/services/` → `app/repositories/` → `app/db/`.

Hướng dẫn chi tiết: `docs/backend_guide.md`. Hợp đồng request/response: `docs/api_contract.md`. Giai đoạn kế tiếp là kiểm thử và thu thập bằng chứng cho STRIDE.

Bộ dependency đã được kiểm tra trên Python 3.12/Linux; chưa xác nhận trực tiếp trên Windows/Python 3.13. Không đóng gói mật khẩu, JWT key hay database cá nhân.
