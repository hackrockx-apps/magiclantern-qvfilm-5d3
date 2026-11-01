# QVFilm 5D3 — Phân tích lỗi MLV Lite Lossless (v0.4.2)

**Trạng thái:** HARDWARE BASELINE PASS / MLV LOSSLESS ASSERT FAIL / NO FIRMWARE PATCH APPROVED.

## Bằng chứng từ LCD của người dùng

- Camera: Canon EOS 5D Mark III; Magic Lantern dev `2025-06-20.5D3.123`, commit `ed3e7c0df`.
- MLV Lite đã nạp; Movie > RAW video hoạt động.
- Menu trước đó: `1920x1080`, `25.000p`, `14-bit lossless`, Pre-record OFF, Rec trigger OFF; người dùng được hướng dẫn hạ độ phân giải cho phép thử. Ảnh chẩn đoán **không xác nhận chính xác độ phân giải đã chọn ngay lúc ghi**, mặc dù màn hình ghi frame size khoảng 1.5 MB.
- Ảnh khi ghi hiển thị `ML ASSERT: 0 at mlv_lite.c:2742 (compress_task), task compress_task`; có nội dung cấp phát double-buffering, khoảng 173 slots, `compress_task stack`.
- Không phải thông báo dropped frames hay tốc độ ghi thẻ thông thường. Mức độ: **RAW recording not accepted**.

## Đối chiếu mã nguồn chính xác

Nguồn **đúng commit đang cài**, không phải fork Arnaud:

https://github.com/reticulatedpines/magiclantern_simplified/blob/ed3e7c0df/modules/raw_video/mlv_lite/mlv_lite.c#L2730-L2743

- Trong `compress_task()`, dòng 2730 gọi `lossless_compress_raw_rectangle(...)`.
- Dòng 2739 nếu `compressed_size < 0 && !RAW_IS_IDLE`, dòng 2741 log `Compression error %d at frame %d`, dòng **2742 `ASSERT(0)`**.
- Do đó lỗi trên LCD chứng minh hàm lossless đã trả về **mã lỗi âm** trong lúc recorder đang hoạt động. Chưa có log chứa mã âm cụ thể.

Nguồn bộ nén:

https://github.com/reticulatedpines/magiclantern_simplified/blob/ed3e7c0df/modules/silent/lossless.c

Các mã âm được hàm trả về:
- `-1`: encoder chưa khởi tạo.
- `-2`: timeout khi chờ semaphore hoàn tất nén (1.000 ms).
- `-3`: dữ liệu đầu ra không có chữ ký JPEG dự kiến.

Chưa thể kết luận nguyên nhân là thẻ SD, cảm biến, RAM hay firmware bị hỏng. Lỗi luồng nén khác với dropped frames do thẻ chậm.

## Hành động an toàn

1. Tắt máy bình thường khi đèn thẻ ngừng hoạt động; nếu treo hoàn toàn, dừng thử và chỉ xử lý pin khi chắc chắn không còn ghi. Bảo toàn file MLV chưa hoàn tất, nếu có.
2. Bật lại, vào Movie > RAW video, tạm chuyển OFF. Kiểm tra Canon still, LiveView và menu vẫn hoạt động.
3. Trên PC (đầu đọc thẻ), **sao lưu riêng các file log mới trong `ML/LOGS/`** và các MLV test (nếu có). Không xóa, không format thẻ; không chia sẻ ROM dump công khai.
4. Thử phép đối chứng **một lần**: chọn Data format **10-bit uncompressed** nếu menu có, Resolution **960x540** hoặc thấp hơn nếu SD chậm, Aspect 16:9, FPS Override OFF (25p), Pre-record OFF, Rec trigger OFF, các mục Advanced không chỉnh. Mục tiêu là tạm *bỏ qua bộ nén*, không phải cấu hình chất lượng chính thức. Nếu 10-bit uncompressed không có, 12-bit uncompressed ở mức thấp hơn; không chọn 14-bit lossless.
5. Chỉ ghi **3–5 giây** nếu LiveView hoạt động và không báo lỗi. Nếu `ML ASSERT` lại xuất hiện, **không thử thêm**; chuyển RAW video OFF khi có thể và chẩn đoán từ log.
6. Nếu quay thành công, ghi nhận file MLV, kích thước và khả năng mở trong MLV App; kết luận tối đa là **UNCOMPRESSED SHORT TEST PASS**, không phải lossless hoặc 1080p/3K PASS.
7. Không thay `mlv_lite.mo` và không cài QVFIL tùy biến vào thẻ ổn định.

## Dữ liệu chẩn đoán cần tiếp theo

- Ảnh màn hình Data format sau khi chuyển sang **uncompressed** và Resolution đã chọn.
- File log mới nhất liên quan crash/assert trong `ML/LOGS/` nếu tồn tại (không gửi `ROM*.BIN`).
- Báo cáo thử 3–5s: chạy được/không, file MLV có/không, dòng `Compression error -N at frame X` nếu có.
- Loại thẻ đang ghi (CF hay SD, model) và liệu có thể ghi RAW không nén mức thấp.

## Kiểm tra firmware tùy biến

Thay `ASSERT(0)` bằng xử lý lỗi không được phép thực hiện vội: có thể để lọt khung hình lỗi hoặc hỏng bộ đệm. Chỉ nghiên cứu vá lỗi an toàn sau khi có mã âm và tái hiện được trên đúng nguồn build 2025; bản fork Arnaud đang sử dụng cho QVFIL UI **không bảo đảm ABI tương thích**.

**Release gate:** LOSSLESS_REPRODUCED, UNCOMPRESSED_CONTROLLED_TEST, LOG_CAPTURE_PENDING. No camera-side firmware patch approved.
