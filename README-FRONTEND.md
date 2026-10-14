# Frontend giai đoạn 1

Giao diện triển khai theo bốn hình đã duyệt: đăng nhập, tài khoản/số dư, chuyển tiền và lịch sử. Màu xanh lá–trắng, tên người dùng Nguyễn Văn A/B/C. Các trang dùng chung base.html và style.css; app.js xử lý thao tác và kết nối dữ liệu.

## Cài và xem ngay trong PowerShell

Tại thư mục repo chứa app/ và scripts/:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-frontend.txt
.\.venv\Scripts\python.exe -m scripts.preview_frontend
```

Nếu .venv đã có thì bỏ lệnh đầu. Mở http://127.0.0.1:5500 bằng trình duyệt. Dùng van_a / van_b / van_c với mật khẩu **Demo@2026!**. Đây chỉ là mật khẩu cho chế độ frontend xem trước, không phải mật khẩu backend.

Thử đăng nhập van_a → xem 1.000.000 đ → chuyển 100.000 đ sang ACC_B → mở lịch sử: có một giao dịch và số dư 900.000 đ. Nút gửi lại cùng yêu cầu không tạo giao dịch mới. Chọn Giao dịch mới để nhập một lần chuyển khác. Đăng xuất rồi đăng nhập van_b để thấy số dư nhận tiền.

Chế độ xem trước dùng sessionStorage; chưa kết nối DB hay gửi yêu cầu tài chính thật. Trạng thái thường giữ qua reload trong cùng tab nhưng kết thúc phiên tab có thể mất dữ liệu. Không dùng kết quả demo để chứng minh kiểm soát STRIDE ở server.

Ctrl+C tại terminal để dừng. Sau khi chỉnh file nguồn, dừng rồi chạy lại preview_frontend để dựng lại HTML/CSS/JS. Không mở trực tiếp templates bằng double-click vì các trang dùng Jinja và đường dẫn /static.

## Nối với backend đang có

Dùng bộ code Python đầy đủ đã cung cấp trước đó. Các file frontend này tương thích với endpoint của bộ code đó. Chạy backend như README chính, mở http://127.0.0.1:8000. Khi FastAPI render, data-mode mặc định là api; app.js gọi API thật. Mật khẩu phải là mật khẩu đã đặt bằng seed_data, không mặc định Demo@2026!.

Không cần sửa app.js để đổi chế độ. Không đổi data-mode của trang backend sang demo; việc mô phỏng chỉ phục vụ quan sát giao diện.

## Phạm vi cập nhật

Gói này chứa app/templates/, app/static/, scripts/preview_frontend.py, requirements-frontend.txt và tài liệu frontend. Sao chép đúng các đường dẫn tương ứng vào repo. Không có mã thay thế backend/database trong gói này.

Xem docs/frontend_guide.md để đọc từng file theo thứ tự.

## File Git cần giữ

Gói kèm .gitignore để bỏ qua .venv/, runtime/, .env và cache. Nếu repo đã có .gitignore do bạn chỉnh, gộp các quy tắc thay vì xóa nội dung cũ.
