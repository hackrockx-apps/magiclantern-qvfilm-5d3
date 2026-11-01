# QVFIL Cinema Overlay v0.5.2 — nghiệm thu trên 5D Mark III

## Nguyên nhân cần phân biệt

Người dùng đã xác nhận v0.5.1 xuất hiện trong Movie và có trạng thái ON. Ảnh LiveView cho thấy chồng chéo giữa Magic Lantern overlay và Canon. Sau khi nhấn Shutter, Canon hiển thị màn hình thông số riêng. Đây **không chứng minh máy đang quay RAW hoặc module đã treo**.

Trong **đúng** mã nguồn `mlv_lite.c` của Magic Lantern 2025:
- `raw_rec_keypress_cbr`: ghi RAW bắt đầu/dừng bằng **MODULE_KEY_LV hoặc MODULE_KEY_REC** (trên 5D3: START/STOP khi gạt sang chế độ quay phim). Shutter không tự khởi động MLV khi **Rec trigger OFF**.
- `raw_rec_should_preview`: **nhấn giữ nửa cò hơn khoảng 500 ms** đảo lựa chọn preview (nếu không ở trong quá trình AF), nên có thể thấy giao diện/khung hình thay đổi. Không ép Canon bỏ xử lý AF/shutter.
- Module quay thử PASS là 1280×720 **10-bit uncompressed**. Trong v0.5.1, biến `BPP_D` có thể hiện **14b RAW** vì macro này mô tả bit depth số hóa cho một đường nén riêng, không phải bit depth thực tế của file uncompressed. v0.5.2 đổi sang **BPP**.

## Những thay đổi v0.5.2

Giữ nguyên chính xác nguồn Magic Lantern dev 2025, commit `ed3e7c0dfacfdeaf3349dee73edf9e3621217462`. Chỉ thay tệp mã nguồn module `mlv_lite.c`, không flash Canon.

- `Movie → QVFIL Cinema HUD` có 3 lựa chọn: `OFF`, `Info bars`, `Cinema overlay`.
- `Info bars`: tương thích chế độ ON = 1 đã lưu từ bản 0.5.1, chỉ đổi lại độ sâu bit chính xác.
- `Cinema overlay`: hai thanh đen tinh gọn trên vùng bitmap LiveView. Trên: QVFIL CINEMA / STBY hoặc REC / FPS. Dưới: độ phân giải thực tế / bit-depth RAW thực tế / ISO. Chữ REC màu đỏ.
- Vẽ tối đa khoảng **1 lần/giây** trong luồng cập nhật status `ShootTask` đã tồn tại; **không vẽ trong VSYNC**, không thay RAW buffer, không cài lại firmware. Chỉ hoạt động khi `Movie LiveView`, `Global Draw ON`, `RAW video ON` và Canon GUI ở trạng thái idle.
- Khi Canon chuyển sang menu hoặc màn hình thông tin do Shutter/AF, QVFIL **không cố chiếm toàn bộ màn hình** và có thể tạm ẩn. Đây là giới hạn an toàn có chủ đích, không hứa luôn hiển thị khi Canon đang vẽ màn hình riêng.
- Chốt chống ASSERT với lossless của v0.5.1 giữ nguyên. **14-bit lossless chưa được sửa/khôi phục; chế độ nén vẫn bị chặn.**

## Nghiệm thu thẻ thử

1. Giữ nguyên thẻ Magic Lantern nền 2025 đang PASS và bản backup ROM. Chỉ dùng thẻ thứ hai đã khởi động Magic Lantern thành công; sao lưu module `ML/MODULES/MLV_LITE.MO` cũ trên thẻ này.
2. Sau khi build ARM và checksum PASS, chép module có thể nhận dạng v0.5.2 lên **đúng thẻ thử**, tắt máy hẳn, rồi khởi động lại. Không chạy Canon Firmware Update.
3. Trong **Modules**, xác nhận `mlv_lite.mo` đã nạp; trong **Movie**, xác nhận `QVFIL Cinema HUD — v0.5.2`.
4. Chọn `Cinema overlay`, `RAW video ON`, `Data format 10-bit uncompressed`, `Rec trigger OFF`, `FPS override OFF`, `Gradual Exposure OFF` (để test không bị thay đổi tự động); **Global Draw ON**.
5. Vào LiveView ở chế độ video. Đợi >1 giây cho thanh cinema xuất hiện. Kiểm tra trước khi quay chữ `STBY`, FPS, resolution, **10b RAW**, ISO. Chụp ảnh giao diện.
6. **Không dùng Shutter để khởi động MLV**. Nhấn nút **START/STOP** phía sau theo cơ chế phím LV/REC của Magic Lantern, xác nhận `REC` đỏ và chỉ báo đang ghi. Ghi 3–5 giây rồi nhấn lại để dừng.
7. Khi dừng, xác minh có file `.MLV` mới và giải mã được trong MLV App; gửi ảnh nếu overlay không chuyển STBY↔REC. Nếu Canon GUI hiện trở lại khi half-shutter, thả nút ra; không cưỡng ép bằng cách sửa firmware, vì hành vi half-shutter preview vốn có trong ML.
8. Nếu treo, báo MODULE ERROR, frame hỏng hay nút ghi không hoạt động, ngừng thử và khôi phục `MLV_LITE.MO` gốc trên thẻ thử; không cài lại firmware.

## Trạng thái

`v0.5.2_SOURCE_AND_ARM_BUILD_PENDING_CAMERA_TEST`

`CANON_MENU_PRESERVED`, `LOSSLESS_COMPRESSION_GUARDED_NOT_FIXED`, `RAW_3K_NOT_VALIDATED`

Ghi chú: Đây là các thành phần tình trạng vận hành/monitor, không tự tăng khả năng cảm biến, không bảo đảm 4K60 hoặc 3K liên tục.
