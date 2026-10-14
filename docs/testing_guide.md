# Giai đoạn 4 — kiểm thử STRIDE và bằng chứng

Gói full giữ frontend, database, backend của ba giai đoạn trước và thêm tests/, scripts/run_experiments.py, hướng dẫn và kết quả tham khảo thực sự đã chạy trong môi trường tạo gói.

## Chạy trên máy của bạn

Mở PowerShell tại thư mục stride-banking chứa requirements.txt. Dùng .venv đã cài; nếu giải nén vào thư mục mới, tạo lại .venv tại đó, không copy môi trường cũ.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m scripts.run_experiments --repeat 10
```

Không cần seed hoặc nhập mật khẩu. Không cần bật uvicorn; có thể giữ server demo đang chạy. Mỗi lượt dùng database/key tạm và mật khẩu ngẫu nhiên riêng; không đọc/ghi runtime/bank.sqlite3. Runner gọi FastAPI trực tiếp bằng TestClient, không gửi HTTP ra ngân hàng hoặc dịch vụ thật.

Pytest kiểm tra xác thực, quyền sở hữu, proof hết hạn/ràng buộc phiên, hạn mức, rollback khi lỗi DB, chống lặp, request đồng thời, restart, rate limit và lỗi không lộ dữ liệu. Runner xuất các ca đo lặp có số dư trước/sau và trace ID để làm bằng chứng.

## Nơi lấy bằng chứng của chính bạn

Mỗi lần chạy sinh một run_id mới:

- evidence/results/<run_id>/results.csv: mở bằng Excel, mỗi hàng là một ca/lượt.
- evidence/results/<run_id>/results.json: cùng kết quả ở định dạng JSON.
- evidence/results/<run_id>/metadata.json: thời gian UTC, phiên bản Python/thư viện, cấu hình phạm vi, số ca đạt và hash code.
- evidence/logs/<run_id>/audit.jsonl: mỗi dòng là một sự kiện audit có run, trace_id, principal, action, decision, reason_code, transaction_id.

Các ca HTTP có trace_id để đối chiếu với audit; ca đồng thời có 10 trace ID phân cách dấu phẩy. Ca kiểm tra audit đọc trực tiếp DB nên cột HTTP là N/A, latency_ms=0 không phải số đo tốc độ audit. Kết quả expected_http là dự kiến, actual_http/passed là thực đo. Nếu có lỗi, giữ kết quả thất bại và ghi giải thích; không sửa passed bằng tay.

## Mapping STRIDE

| Nhóm | Mã ca runner | Điều quan sát |
|---|---|---|
| S — giả mạo | AC01_INVALID_TOKEN, AC01_WRONG_PASSWORD | 401; số dư giữ nguyên |
| T — sửa đổi | AC04_TAMPER_AFTER_REAUTH, AC03_CHANGED_PAYLOAD | 403/409; không trừ tiền |
| R — chối bỏ | AC06_AUDIT_CORRELATION_NO_SECRETS | Giao dịch thành công có transaction_id; từ chối có trace ID tương ứng |
| I — lộ thông tin | AC02_OTHER_OWNER, AC02_BAD_JSON_NO_ECHO, AC06_AUDIT_CORRELATION_NO_SECRETS | Chặn truy cập chéo; lỗi không echo đầu vào; audit không có secret đã dùng |
| D — từ chối dịch vụ | AC05_OVER_RATE, AC05_BODY_LIMIT | 429/413; số dư giữ nguyên |
| E — nâng quyền | AC05_CUSTOMER_ADMIN, AC05_ROLE_INJECTION | Customer không đọc audit quản trị; field role/user_id bị từ chối |

Ca đối chứng: AC01_VALID_LOGIN, AC02_VALID_OWNER. AC03_CONCURRENT_10: 10 request cùng key tạo đúng một giao dịch, 1 phản hồi 201 và 9 phản hồi 200, tổng tiền bảo toàn. AC03_REPLAY/AFTER_RESTART: lấy kết quả cũ và không chuyển thêm tiền. AC04_MISSING_REAUTH: 403. AC05_WITHIN_RATE: đối chứng trước khi vượt rate.

Runner tăng ngưỡng login/transfer lên 1.000 để tách thử nghiệm nghiệp vụ khỏi giới hạn tần suất; phần thử rate dùng một app mới với giới hạn transfer=2/60 giây. Đây là cấu hình thực nghiệm, không thay đổi mặc định của server demo.

## Trình bày trước giảng viên

1. Chạy pytest và runner; ghi lại thư mục run_id của bạn.
2. Chọn AC02_OTHER_OWNER: cho thấy HTTP 403, số dư không đổi; tìm trace_id đó trong audit.jsonl để thấy DENY/ACCOUNT_ACCESS_DENIED.
3. Chọn AC03_CONCURRENT_10: cho thấy đúng một lần trừ/cộng, các phản hồi dùng cùng giao dịch. Đây là gửi lặp đồng thời với cùng idempotency key, không phải stress test toàn hệ thống.
4. Chọn AC04_TAMPER_AFTER_REAUTH: bằng chứng cho 100.000 VND không cho phép chuyển 200.000 VND.
5. Chọn AC05_OVER_RATE và AC05_CUSTOMER_ADMIN: chỉ ra giới hạn yêu cầu và kiểm tra vai trò.
6. Trong báo cáo ghi môi trường, commit Git của bạn, người chạy, ngày chạy, dữ liệu giả lập, số ca đạt/tổng, giới hạn và link file bằng chứng. Chụp màn hình app/Terminal trên máy bạn khi cần minh họa; ảnh không thay thế CSV/log.

Thư mục evidence/reference_stage4/ chứa kết quả tham khảo trên môi trường tạo gói, không phải kết quả nhóm tự chạy. Không dùng chúng để khẳng định đã kiểm tra Windows hoặc triển khai cloud. Không có review chéo được thực hiện thay nhóm; dùng mẫu review trống và điền khi người khác thực sự kiểm tra.

## Giới hạn

Đạt các ca này không chứng minh toàn bộ hệ thống an toàn. Chưa kiểm thử hạ tầng cloud/TLS/IAM, DDoS thực, MFA, log WORM hoặc hiệu năng mạng thật. Rate limiter RAM bị reset khi restart; audit SQLite có thể bị sửa bởi người có quyền file. Các hash chỉ hỗ trợ nhận diện phiên bản code, không phải chữ ký chứng minh chống sửa bằng chứng.
