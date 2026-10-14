# STRIDE Banking — bản tổng hợp 3 giai đoạn

Bộ code frontend (giao diện), database (cơ sở dữ liệu), backend (xử lý phía máy chủ) được ghép vào cùng dự án Python. Không cần giải nén ba gói riêng nữa. Đây là nguyên mẫu ngân hàng giả lập chạy local bằng FastAPI và SQLite.

## Chạy trên Windows / PowerShell

Giải nén ZIP, mở Terminal tại thư mục `stride-banking` chứa `app`, `scripts`, `data` và `requirements.txt`.

```powershell
bước 1 : vào đúng thư mục dự án , dán cái này vào terminal
cd "C:\Users\User\Downloads\STRIDE-Full-Frontend-Database-Backend\stride-banking"                 #đây là đường dẫn thư mục vào stride banking tùy theo thư mục ở đâu mà thay đổi" ví dụ khi đổi tên thư mục lưu C:\Users\User\Downloads\STRIDE\stride-banking
Test-Path .\requirements.txt
bước 2 : kiểm tra bản Python Launcher — chương trình chọn bản Python trên Windows — có thể giúp tránh bản đang lỗi:
py -0p
py -c "import sys, encodings; print(sys.executable); print(sys.version)"

bước 3 : tạo môi trường ảo :
python -m venv .venv
bước 4: chạy từng lệnh
.\.venv\Scripts\python.exe -m pip install -r requirements.txt  #Lệnh cài thư viện , đợi cài xong hết thư viện mới dùng lệnh tiếp theo
.\.venv\Scripts\python.exe -m scripts.seed_data                #lệnh này sẽ hỏi mật khẩu dùng chung cho các tài khoản mẫu : nhập 10 ký tự   . lưu ý khi nhập mật khẩu có lúc sẽ không hiện mật khẩu chỉ cần nhấn enter sau khi nhập mật khẩu
.\.venv\Scripts\python.exe -m scripts.reset_data               #lệnh này dùng để reset lại các số dư , giao dịch , phiên và mật khẩu của DB demo đã sử dụng trước đó
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000  # lệnh dùng để khởi tạo server link : http://http://127.0.0.1:8000
```
ấn crlt+C để tắt server 

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m scripts.seed_data
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Nếu đã có .venv, bỏ lệnh tạo môi trường. Nếu database đã có dữ liệu, bỏ lệnh seed. Seed hỏi mật khẩu ít nhất 10 ký tự và từ chối ghi đè database hiện có. Giữ database cũ nếu đang muốn giữ lịch sử.

Mở http://127.0.0.1:8000/ rồi đăng nhập van_a, van_b hoặc van_c bằng mật khẩu đã đặt lúc seed. Tài liệu API ở http://127.0.0.1:8000/api-docs.

Với dữ liệu mới: Nguyễn Văn A / ACC_A có 1.000.000 VND; Nguyễn Văn B / ACC_B có 500.000 VND; Nguyễn Văn C / ACC_C có 200.000 VND. Đây là số dư giả lập.

## Các phần trong dự án

| Đường dẫn | Vai trò |
|---|---|
| app/templates/ | Các trang HTML dùng Jinja2 |
| app/static/ | CSS, JavaScript và thư mục hình ảnh |
| app/db/ | Schema SQLite, kết nối và transaction |
| app/repositories/ | Truy vấn dữ liệu |
| app/schemas/ | Kiểm tra dữ liệu vào/ra API |
| app/security/ | Mật khẩu, JWT, quyền truy cập, rate limit |
| app/services/ | Nghiệp vụ đăng nhập, tài khoản, chuyển tiền và nhật ký |
| app/routers/ | Các đường dẫn API |
| app/config.py, app/main.py | Cấu hình và khởi chạy ứng dụng |
| scripts/ | Tạo dữ liệu, kiểm tra database và xem riêng frontend |
| data/ | Dữ liệu người dùng mẫu |
| docs/ | Hướng dẫn từng phần và hợp đồng API |

Đọc README-FRONTEND.md, README-DATABASE.md, README-BACKEND.md để hiểu từng giai đoạn; trong bản tổng hợp không cần thực hiện bước ghép lại các gói.

Nếu muốn chỉ xem giao diện: chạy `.\.venv\Scripts\python.exe -m scripts.preview_frontend`, mở cổng 5500. Bản này dùng dữ liệu giả trong trình duyệt và mật khẩu Demo@2026!, không ghi vào SQLite. Để kiểm tra ứng dụng tích hợp, dùng cổng 8000 và mật khẩu đã seed.

## Phạm vi và kiểm tra

Gói tổng hợp giữ nguyên code ba giai đoạn. Trước khi đóng gói, bản ghép của ba gói đã đạt 23 bài kiểm thử và kiểm tra tải trang/tài nguyên/API trên Python 3.12/Linux. Chưa xác nhận trực tiếp trên Windows/Python 3.13. Bản này đã bổ sung tests/, runner thực nghiệm và hướng dẫn README-TESTING.md cho giai đoạn 4.

Chưa triển khai cloud hoặc MFA; nhập lại mật khẩu là xác thực lại. Không có mật khẩu cá nhân, database, JWT key hay môi trường .venv được đóng gói. Các file runtime/ được tạo khi chạy và được .gitignore bỏ qua. Không đưa runtime/, .env hoặc .venv/ lên Git.
