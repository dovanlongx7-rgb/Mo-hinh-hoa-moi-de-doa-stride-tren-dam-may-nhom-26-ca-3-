# Hướng dẫn học và triển khai frontend

## Thứ tự và trách nhiệm

| Bước | Đường dẫn | Nội dung đã triển khai |
|---|---|---|
| 1 | app/templates/base.html | Header, menu, footer, icon SVG chung, khung cho bốn trang |
| 1 | app/static/css/style.css | Màu sắc, font hệ thống, form, bảng, trạng thái, bố cục màn hình nhỏ |
| 2 | app/templates/login.html | Username, password, lỗi đăng nhập và ghi chú demo |
| 3 | app/templates/account.html | Chủ tài khoản, số dư, ID và đường dẫn chuyển tiền/lịch sử |
| 4 | app/templates/transfer.html | Nguồn/đích, số tiền, nhập lại mật khẩu, kết quả và giao dịch mới |
| 5 | app/templates/history.html | Số dư hiện tại, bảng lịch sử, trạng thái rỗng |
| 6 | app/static/js/app.js | Điều hướng, adapter demo/API, đăng nhập, tải dữ liệu, chuyển tiền và lịch sử |
| Phụ trợ | scripts/preview_frontend.py | Dựng Jinja thành HTML và phục vụ trên loopback:5500 |
| Phụ trợ | requirements-frontend.txt | Jinja2, đủ để xem trước độc lập |

## Cách đọc mã

Trong HTML: đọc form/label/input/button trước; sau đó xem các block kế thừa base.html. Trong CSS: đọc :root (màu), shell/sidebar (bố cục), card/input (thành phần), cuối cùng media query (màn hình nhỏ). Trong app.js: phần 1 cấu hình → 2 adapter demo → 3 API thật → 4 điều hướng/login → 5 account → 6 transfer → 7 history. Chú thích tiếng Việt đi cùng mỗi nhóm.

## Hợp đồng kết nối

| Thao tác | API |
|---|---|
| Đăng nhập | POST /api/auth/login, JSON username/password |
| Danh tính | GET /api/auth/me |
| Danh sách tài khoản | GET /api/accounts |
| Xác thực lại | POST /api/transfers/reauth, JSON source_account_id/target_account_id/amount/password |
| Chuyển tiền | POST /api/transfers, JSON intent + reauth_proof, header Idempotency-Key |
| Lịch sử | GET /api/accounts/{id}/history |
| Đăng xuất | POST /api/auth/logout |

Giao diện nhận danh tính/số dư từ API trong chế độ api. Mẫu A/B/C chỉ dùng gợi ý người nhận của nguyên mẫu hiện tại; chưa có API tìm danh bạ người nhận. Tên tài khoản mở rộng cần bổ sung từ backend, không mặc nhiên tra trong danh sách cứng.

## Trạng thái giao diện cần hiểu

- Đang tải: tài khoản, số dư, history; nút chuyển tiền bị khóa khi chưa biết nguồn.
- Sai mật khẩu/xác nhận: hiển thị thông báo, cho thử lại; không echo mật khẩu.
- Chuyển thành công: hiện mã giao dịch, cho tạo giao dịch mới hoặc hỏi lại kết quả cũ.
- Chưa biết kết quả vì timeout/5xx: giữ nguyên intent/key/proof, khóa sửa số tiền/người nhận và gửi lại cùng yêu cầu. Đổi key ngay lúc này có nguy cơ tạo giao dịch mới.
- HTTP 4xx rõ ràng ngoài 429: giải phóng yêu cầu để người dùng sửa/xác thực lại.
- Lịch sử rỗng: có hướng dẫn, không bịa dữ liệu giao dịch.

Token và pending proof được giữ trong sessionStorage cho nguyên mẫu; không lưu mật khẩu. Đây chưa phải thiết kế quản lý phiên production. Kiểm tra input trong JS giúp người dùng thao tác; backend vẫn là nơi quyết định quyền, số dư, hạn mức và transaction.

## Cách kiểm tra bằng tay

1. Sai password không vào tài khoản; đúng password vào được.
2. Chuyển 100.000 đ A→B; số dư A từ 1.000.000 xuống 900.000.
3. Gửi lại cùng yêu cầu; không trừ thêm, chỉ một dòng lịch sử.
4. Reload trang chuyển tiền; key yêu cầu trước được giữ để hỏi lại.
5. Đăng nhập B cùng tab; số dư tăng 100.000 và lịch sử thấy giao dịch nhận.
6. Mở ở màn hình hẹp; menu chuyển ngang, form không bị tràn.
7. Chạy với backend; body data-mode phải là api, không dùng password demo nếu DB được seed với password khác.

## Giới hạn

Demo là mô phỏng trong một tab. Không chứng minh MFA, mTLS, cloud IAM hoặc chống truy cập DB. Không thực hiện tấn công lên dịch vụ thật. Không có reset tự động trong backend; xóa sessionStorage demo chỉ reset dữ liệu mô phỏng.

## Xác minh trong môi trường tạo gói

Đã chạy Chromium headless: đăng nhập sai/đúng, tài khoản, lịch sử rỗng, chuyển tiền và replay/reload trong demo; cùng frontend gọi backend thật; mô phỏng mất phản hồi sau commit rồi reload/retry, không ghi nợ thêm. Không có lỗi JavaScript phát sinh. Hai trang account/transfer ở 390px không tràn ngang; đã kiểm tra hình hiển thị desktop và mobile. Bộ test backend hiện có vẫn đạt 23/23. Chưa kiểm thử trực tiếp trên Windows/Visual Studio.
