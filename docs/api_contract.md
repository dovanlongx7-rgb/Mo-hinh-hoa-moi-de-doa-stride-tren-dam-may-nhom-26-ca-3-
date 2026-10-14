# Hợp đồng API frontend ↔ backend

Base URL cùng origin: `http://127.0.0.1:8000`. Body JSON dùng `Content-Type: application/json`. API bảo vệ dùng `Authorization: Bearer <access_token>`. Không gửi `user_id` hoặc `role` để quyết định quyền; server tự xác định.

| Method | Đường dẫn | Quyền | Kết quả thành công |
|---|---|---|---|
| POST | /api/auth/login | Công khai, rate limit | 200: access_token, token_type, expires_in, user |
| GET | /api/auth/me | Phiên hợp lệ | 200: id, username, full_name, role |
| POST | /api/auth/logout | Phiên hợp lệ | 200: message; phiên bị thu hồi |
| GET | /api/accounts | Phiên hợp lệ | 200: danh sách tài khoản của người dùng |
| GET | /api/accounts/{account_id} | Chủ tài khoản | 200: id, user_id, balance |
| GET | /api/accounts/{account_id}/history | Chủ tài khoản | 200: tối đa 100 giao dịch, mới nhất trước |
| POST | /api/transfers/reauth | Phiên hợp lệ, chủ nguồn | 200: reauth_proof, expires_in, method, note |
| POST | /api/transfers | Phiên hợp lệ, chủ nguồn | 201 giao dịch mới; 200 phát lại |
| GET | /api/admin/audit | Operator | 200: tối đa 200 sự kiện |

## Body đăng nhập

```json
{"username":"van_a","password":"<mat-khau-da-seed>"}
```

Giữ token cho phiên sử dụng; không in token hoặc password vào báo cáo/log. Response `user` không chứa hash mật khẩu hoặc session_id nội bộ.

## Body xác thực lại

```json
{"source_account_id":"ACC_A","target_account_id":"ACC_B","amount":100000,"password":"<mat-khau-da-seed>"}
```

Lấy `reauth_proof` từ response. Phương thức là `password_reentry`, không phải MFA/OTP.

## Body chuyển tiền

Thêm header `Idempotency-Key: <mot-UUID-duy-nhat-cho-giao-dich>` và gửi:

```json
{"source_account_id":"ACC_A","target_account_id":"ACC_B","amount":100000,"reauth_proof":"<bang-chung-tu-reauth>"}
```

Response gồm `transaction` và `replayed`. Transaction có `id`, `user_id`, `source_account_id`, `target_account_id`, `amount`, `created_at`, `day_utc`. Giao dịch mới: `replayed=false`, HTTP 201. Phát lại đúng key/nội dung: `replayed=true`, HTTP 200 và cùng transaction id. Không chứa số dư mới; frontend lấy lại tài khoản khi cần.

## Lỗi

Dạng lỗi được ứng dụng xử lý:

```json
{"error":"ACCOUNT_ACCESS_DENIED","trace_id":"<UUID>"}
```

| HTTP | Mã điển hình | Hành động frontend |
|---|---|---|
| 401 | INVALID_CREDENTIALS, AUTH_REQUIRED, INVALID_SESSION | Thông báo đăng nhập sai hoặc yêu cầu đăng nhập lại |
| 401 | REAUTH_PASSWORD_INVALID | Cho nhập lại mật khẩu; giữ phiên hiện tại |
| 403 | ACCOUNT_ACCESS_DENIED, ROLE_DENIED | Báo không có quyền |
| 403 | REAUTH_REQUIRED, REAUTH_INVALID | Lấy bằng chứng hợp lệ; không tự đổi key của giao dịch chưa rõ kết quả |
| 409 | IDEMPOTENCY_CONFLICT | Không tự gửi lại bằng key mới; đối chiếu nội dung |
| 413 | BODY_TOO_LARGE | Giảm kích thước yêu cầu |
| 422 | INVALID_INPUT, INVALID_IDEMPOTENCY_KEY | Kiểm tra định dạng/field |
| 422 | SAME_ACCOUNT, TARGET_INVALID, PER_TRANSFER_LIMIT, DAILY_LIMIT, INSUFFICIENT_FUNDS | Hiển thị lý do nghiệp vụ |
| 429 | RATE_LIMITED | Chờ thời gian Retry-After |
| 500 | INTERNAL_ERROR | Giữ trạng thái chưa rõ kết quả, dùng cùng key để truy vấn bằng phát lại |

X-Trace-ID được server cấp cho mỗi request. Khi timeout/mất kết nối, trình duyệt không biết giao dịch đã commit chưa; giữ intent/key và dùng luồng thử lại cùng giao dịch. Không coi lỗi mạng là bằng chứng rằng tiền chưa chuyển.
