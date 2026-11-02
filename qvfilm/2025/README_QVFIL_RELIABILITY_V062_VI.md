# QVFIL Media Engine v0.6.2 — Reliability Monitor / Giải thích băng thông thực tế

## Checkpoint người sử dụng (2026-11-02)

- Canon EOS 5D Mark III, Magic Lantern 2025-06-20 / 5D3.123.
- **v0.6.0**: Anh quay hơn 20 giây trên SanDisk Extreme CF 64 GB UDMA7, chủ động dừng và xác nhận MLV App phát file `M02_1652.mlv` ổn; không có file gốc trong cuộc trao đổi để kiểm tra dropped frames tự động.
- **v0.6.1**: Anh xác nhận các tên mục Movie hiển thị bình thường. **Đây là PASS của tên menu, không tự động chứng minh giá trị Flow/I/O đã đúng hoặc quay liên tục vài phút.**
- Trước đây thẻ Lexar UHS-II SD tự ngắt khoảng 11 giây vì thiếu khả năng xả buffer. Khi dùng CF, clip thử >20 giây không tự ngắt.

## Lỗi logic cần điều chỉnh

Ở v0.6.0 và v0.6.1, `QVFIL Media Engine` báo thiếu băng thông nếu `Flow < 1.2 × Demand`. Đây là điều kiện **sai về ý nghĩa dữ liệu**: Flow được tính từ `written_total / elapsed_capture_time`, trong chế độ ghi đều đặn luôn gần bằng RAW Demand; thẻ cực nhanh cũng không thể tăng `Flow` lên 120% chỉ vì không có thêm frame để ghi. Vì vậy điều kiện cảnh báo nói trên có nguy cơ báo sai ngay cả trên CF hoạt động tốt.

## v0.6.2 sửa GIAO DIỆN, KHÔNG SỬA BỘ GHI

- Dùng `I/O` — `written_total / writing_time` khi tác vụ FIO thực sự hoạt động — làm **proxy ước tính** khả năng xả dữ liệu của writer. **Không được diễn giải đây là tốc độ CF duy trì tối đa**: phép đo này còn phụ thuộc cache, filesystem, overhead và tính chất clip.
- `Movie > QVFIL Media Engine`: hiển thị `CF Need:xx.x` hoặc `SD Need:xx.x`; bên phải `I/O:xx.x` sau khi có một phép quay trên cùng ký tự ổ. Nếu chưa quay, sẽ hiện NO SAMPLE.
- Thứ tự mức cảnh báo:
  1. Nếu `Last:BUFFER`, hiển thị BUFFER FULL của lần ghi gần nhất (ưu tiên hơn các cảnh báo tốc độ).
  2. Nếu `Last:WRITE`, thông báo lỗi ghi file cần kiểm tra thẻ/filesystem.
  3. Nếu chưa đo được tốc độ, báo không có mẫu hợp lệ.
  4. Nếu thời lượng mẫu ngắn dưới 30 giây, báo mẫu chưa đủ thời gian.
  5. Nếu `I/O < 120% × Need`, cảnh báo **ước tính** dự phòng ghi dưới 20%.
  6. Nếu đạt mức ước tính, vẫn yêu cầu MLV App và bài quay ít nhất 3 phút, **không tuyên bố PASS lâu dài**.
- `Movie > QVFIL Recording Report`: giữ nguyên `Flow`, `I/O`, thời gian ghi, hàng đợi pending và mã BUFFER/WRITE/NONE; làm rõ Flow là lưu lượng trong phiên quay, không phải tốc độ tối đa của thẻ.
- Giữ nguyên từng dòng hàm `raw_video_rec_task()` từ v0.6.1. Không sửa kích thước buffer, chế độ hiển thị HUD, bitrate/bit-depth, logic ghi CF/SD, thư viện Canon, SD Clock hay bootflag. Vẫn khóa đường lossless gây ASSERT.
- Mọi đo lường chỉ tồn tại trong RAM; nếu đổi thẻ vật lý trong cùng khe, mẫu cũ có thể không còn đại diện, cần quay lại. Không có chức năng overclock hoặc tạo file benchmark trong bản này.

## Nghiệm thu gọn trên thẻ thử

1. Chỉ thay `ML/MODULES/MLV_LITE.MO` ở thẻ đã sao lưu và có khả năng khởi động; giữ nguyên SD gốc và các file ROM backup. Xác nhận SHA-256. **Không** dùng Canon Firmware Update.
2. Vào Movie, xác nhận nhãn `QVFIL v0.6.2`. Kiểm tra tên menu, `QVFIL Media Engine` và `QVFIL Recording Report` không có ký tự `AAAA` hoặc `u.u`; tên từ v0.6.1 được giữ nguyên.
3. Gắn SanDisk CF 64 GB, `RAW ON`, 10-bit uncompressed, 1280×720/25p, FPS override OFF, Gradual Exposure OFF, HUD OFF, Rec trigger OFF, Pre-record OFF. Kiểm tra Storage Check báo CF. `Media Engine` có thể báo NO SAMPLE sau boot.
4. Quay 30–40 giây và chủ động dừng; đợi flush hoàn tất. `Recording Report` phải có `Flow`, `I/O`, elapsed và pending hợp lý. `Media Engine` phải dùng `I/O` để đánh giá thay vì Flow.
5. Nếu clip được MLV App phát mượt, thử trên cùng CF 1600×900/25p, 10-bit với 30 giây rồi tăng lên 1 phút, 3 phút. Báo kết quả từng chế độ. Không coi cảnh báo màu xanh đồng nghĩa chất lượng khung hình PASS.
6. Nếu lỗi tự ngắt, treo, ghi không thành công hoặc số liệu phi lý (ví dụ `I/O:0.0` trong khi file MLV được ghi đầy đủ), dừng nghiệm thu, lưu ảnh màn hình và phục hồi module v0.6.1. Không tự tăng xung SD hoặc bỏ qua dừng an toàn.

## Gating
`v0.6.1_MENU_NAMES_USER_PASS` · `v0.6.0_CF_SHORT_MLV_USER_PASS` · `v0.6.2_SOURCE_ARM_PENDING` (cập nhật sau CI) · `v0.6.2_HARDWARE_PENDING` · `NO_SD_OVERCLOCK` · `LOSSLESS14_GUARDED`.
