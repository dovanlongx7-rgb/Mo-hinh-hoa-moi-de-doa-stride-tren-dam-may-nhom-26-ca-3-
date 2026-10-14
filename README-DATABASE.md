# Database giai đoạn 2

Đây là các file dữ liệu của cùng nguyên mẫu STRIDE. SQLite lưu database tại `runtime/bank.sqlite3`; bảy bảng tương thích với backend Python đã cung cấp. Không dùng database này cho tiền thật.

## Cài và chạy riêng

Tại thư mục repo có app/, scripts/ và data/:

```powershell
# Nếu đã có .venv từ frontend thì bỏ lệnh đầu.
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-database.txt
.\.venv\Scripts\python.exe -m scripts.seed_data
.\.venv\Scripts\python.exe -m scripts.inspect_database
```

`seed_data` hỏi mật khẩu ít nhất 10 ký tự. Tự đặt mật khẩu này cho van_a, van_b, van_c; chữ nhập không hiện trên terminal. Mật khẩu demo frontend **Demo@2026!** không tự động trở thành mật khẩu database.

Sau seed mới: users=3, accounts=3, các bảng nghiệp vụ khác=0. Tài khoản ACC_A/ACC_B/ACC_C lần lượt có 1.000.000/500.000/200.000 VND. Inspector cần hiện passwords_argon2id=true, integrity_ok=true, foreign_key_violations=0. Không in hash đầy đủ, mật khẩu, token hoặc khóa.

Nếu DB đã có dữ liệu, seed từ chối ghi đè. Đừng reset để làm mất lịch sử nếu đang muốn giữ dữ liệu. `reset_data` chỉ dùng khi muốn tạo lại môi trường thử: dừng backend trước, chạy `python -m scripts.reset_data`, đọc đường dẫn được in và gõ RESET. Mật khẩu sẽ được hỏi lại.

## File đi kèm

- app/config.py: đường dẫn và cấu hình hiện có của project.
- app/db/models.py: định nghĩa schema.
- app/db/connection.py: kết nối và transaction.
- app/repositories/: truy vấn người dùng, tài khoản và giao dịch.
- app/security/passwords.py: băm mật khẩu dùng khi seed.
- data/sample_accounts.json: tên và số dư giả lập, không có mật khẩu.
- scripts/seed_data.py, reset_data.py, inspect_database.py: tạo/reset/đọc kiểm tra.
- docs/database_guide.md: bảng, khóa và quan hệ.

Copy nội dung trong stride-banking vào repo theo đúng đường dẫn. Các file config.py, passwords.py và repository là cùng bộ code trước đó, được kèm để giai đoạn database chạy riêng. Nếu đã sửa những file này trên máy, đối chiếu trước khi ghi đè. Giữ .gitignore bỏ qua .env, runtime/, .venv/ và cache; không đưa DB/khóa lên Git.

## Giới hạn

Đây là một file SQLite local, chứa các kho logic D1/D2/D4. Chưa có DB server/cloud, tách quyền DB giữa dịch vụ, mã hóa file DB hoặc WORM. Database kiểm tra khóa/ràng buộc đơn giản; quyền sở hữu, xác thực lại, hạn mức và chống lặp phải được backend xử lý cùng transaction. Không dùng kết quả inspector để tuyên bố toàn bộ ứng dụng an toàn.
