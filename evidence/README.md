# Minh chứng thực nghiệm

Chỉ lưu minh chứng tạo ra từ phép thử thực tế của nhóm. Không điền trước kết quả dự kiến thành kết quả đạt.

## Thư mục

- `results/`: CSV/JSON dữ liệu đo.
- `logs/`: JSONL hoặc log đã lọc bí mật.
- `screenshots/`: ảnh giao diện minh họa.
- `reviews/`: review chéo và thông tin tái tạo.

## Mỗi phép thử ghi

Mã ca, commit, cấu hình, dữ liệu ban đầu, bước chạy, kết quả mong đợi, kết quả thực tế, người chạy, reviewer và đường dẫn file. Ảnh không thay thế CSV/log đo.

Trước khi commit, kiểm tra không có mật khẩu, token, khóa riêng, dữ liệu cá nhân thật, file `.env`, cache, virtual environment hoặc database local. Nếu log có giá trị bí mật, xóa/che trước khi lưu; không đưa raw secret lên Git.
