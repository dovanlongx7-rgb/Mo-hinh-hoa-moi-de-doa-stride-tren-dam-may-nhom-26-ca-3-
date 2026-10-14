# Hướng dẫn backend

## Vai trò từng bộ file

| Đường dẫn | Vai trò | Nên đọc/triển khai |
|---|---|---|
| app/main.py | Khởi tạo FastAPI, trang giao diện, middleware, lỗi và trace ID | 1 |
| app/schemas/auth.py, account.py, transfer.py | Định dạng dữ liệu vào/ra; từ chối field thừa | 2 |
| app/security/passwords.py, tokens.py | Argon2id và JWT HS256 | 3 |
| app/security/permissions.py | Kiểm tra phiên, chủ tài khoản và vai trò | 4 |
| app/security/rate_limit.py | Giới hạn tần suất trong một tiến trình | 5 |
| app/services/auth_service.py | Đăng nhập và thu hồi phiên khi đăng xuất | 6 |
| app/services/account_service.py | Trả tài khoản/lịch sử thuộc người dùng | 7 |
| app/services/transfer_service.py | Xác thực lại, hạn mức, chuyển tiền và chống lặp | 8 |
| app/services/audit_service.py | Nhật ký theo danh sách trường cho phép | 9 |
| app/routers/auth.py, accounts.py, transfers.py | Nhận HTTP, gọi service và trả kết quả | 10 |
| app/config.py | Đường dẫn và các giá trị mặc định | Dùng chung database |

Các file repository và kết nối database đã nằm trong gói giai đoạn 2. Frontend phải gọi đường dẫn API trong `docs/api_contract.md`; không trực tiếp cập nhật SQLite.

## Luồng xử lý

Đăng nhập: schema kiểm tra đầu vào → giới hạn theo IP → xác minh hash mật khẩu → lưu phiên → phát JWT. Mọi API bảo vệ đều kiểm tra chữ ký, claim JWT và phiên trong database. Danh tính lấy từ token và dữ liệu server.

Xem tài khoản/lịch sử: kiểm tra phiên → kiểm tra quyền sở hữu → truy vấn dữ liệu. Không tồn tại hoặc thuộc người khác cùng nhận 403 `ACCOUNT_ACCESS_DENIED`.

Chuyển tiền: tạo bằng chứng nhập lại mật khẩu cho đúng tài khoản nguồn, tài khoản đích, số tiền và phiên; sau đó gửi yêu cầu chuyển cùng UUID `Idempotency-Key`. Backend kiểm tra và ghi trừ tiền, cộng tiền, giao dịch, khóa chống lặp, tiêu thụ bằng chứng và nhật ký thành công trong cùng transaction SQLite. Lỗi trước commit làm rollback.

Nếu mất phản hồi sau khi server đã commit, gửi lại **cùng UUID và cùng nội dung giao dịch** để nhận kết quả cũ. Không đổi UUID để thử lại giao dịch chưa rõ kết quả. Một UUID với nội dung khác bị từ chối 409. Bằng chứng hết hạn hoặc đã dùng không thể tạo giao dịch mới; phát lại giao dịch đã commit được tra cứu trước bước kiểm tra bằng chứng.

## Chính sách mặc định

| Chính sách | Giá trị |
|---|---|
| Thời gian JWT/phiên | 1.800 giây |
| Thời gian bằng chứng nhập lại mật khẩu | 180 giây |
| Hạn mức mỗi giao dịch | 300.000 VND |
| Hạn mức tổng tiền gửi mỗi người/ngày | 600.000 VND; ngày UTC |
| Đăng nhập | 5 yêu cầu/IP/60 giây |
| Nhập lại mật khẩu | 5 yêu cầu/người/60 giây |
| Chuyển tiền | 10 yêu cầu/người/60 giây, gồm yêu cầu phát lại |
| Kích thước body | Tối đa 16.384 byte |

Các ngưỡng ở `Settings` trong `app/config.py`. Biến môi trường hiện chỉ ghi đè đường dẫn database và key, không ghi đè các hạn mức này. Tiền là số nguyên VND; boolean, số thực, số âm, 0 đều không hợp lệ.

## Liên hệ STRIDE

| Nhóm | Kiểm soát được minh họa |
|---|---|
| S — giả mạo | Mật khẩu băm, JWT có chữ ký, kiểm tra phiên |
| T — sửa đổi | Schema, transaction, fingerprint gắn bằng chứng với giao dịch |
| R — chối bỏ | Trace ID và nhật ký giao dịch cùng transaction |
| I — lộ thông tin | Quyền sở hữu, lỗi rút gọn, không ghi mật khẩu/token vào audit |
| D — từ chối dịch vụ | Rate limit và giới hạn body |
| E — nâng quyền | Kiểm tra chủ sở hữu và vai trò operator tại server |

Đây là minh họa kiểm soát, không chứng minh đã xử lý hết STRIDE. Nhập lại mật khẩu không phải MFA. Rate limit dùng RAM, mất khi restart và không chia sẻ giữa nhiều worker. Audit trong SQLite không chống sửa kiểu WORM; lỗi ghi audit của request có thể chỉ được báo trong log, còn nhật ký chuyển tiền thành công nằm trong transaction tài chính. Chưa có hạ tầng cloud, TLS, Keycloak, OPA hay quản lý khóa chuyên dụng. Không có operator seed sẵn; ba người dùng mẫu đều là customer.

## Xử lý lỗi thường gặp

- `No module named ...`: dùng đúng `.venv\Scripts\python.exe` và cài `requirements.txt`.
- Thiếu thư mục static/templates hoặc module db/repositories: chưa ghép đủ gói frontend/database.
- 401 khi đăng nhập: dùng mật khẩu đã seed, kiểm tra username `van_a`, `van_b`, `van_c`.
- 429: chờ theo header `Retry-After`; không tắt kiểm soát để che lỗi.
- Cổng 8000 đang được dùng: dừng tiến trình cũ bằng Ctrl+C rồi chạy lại.
- Không commit `runtime/`, `.env`, `.venv/` lên Git; database và khóa local được tạo trên máy chạy.
