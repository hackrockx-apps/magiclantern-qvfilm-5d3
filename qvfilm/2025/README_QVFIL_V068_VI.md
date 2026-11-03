# QVFIL v0.6.8 – Read-only Lossless Diagnostics (Canon EOS 5D Mark III / 1.2.3)

## Mốc đã nghiệm thu
- QVFIL **v0.6.6** là bản đang hoạt động, người dùng xác nhận **HARDWARE PASS**.
- RAW uncompressed đã được người dùng nghiệm thu ở các vòng trước; các lần thử v0.6.3 ghi nhận 1920×1080/4 phút và mở MLV được. Không suy diễn số frame-drop từ ảnh LCD.
- Firmware Canon công khai **1.2.3** đã được người dùng xác nhận.
- Người dùng xác nhận đã **tạo bản sao đầy đủ thẻ SD/CF**. Hiện chưa có checksum hay kiểm chứng khôi phục từ bản sao trong hồ sơ; **không** ghi là restored/verified.
- v0.6.7 đã phân tích lỗi **Lossless 14-bit ASSERT** và kiểm thử mô hình host về fail-closed, nhưng chưa chứng minh việc dọn hàng đợi và finalize thật của module.

## Tính năng có trong v0.6.8

### Movie → QVFIL Lossless Diag
- Hiển thị **bit depth × độ phân giải** hiện tại.
- Hiển thị **LJ OFF** nếu đang dùng RAW không nén, **LJ BLOCKED** nếu người dùng chọn nén trên 5D3, **RAW OFF** nếu RAW chưa bật.
- Không thử chạy compressor, không viết file, không cấp phát bộ nhớ, không gọi encoder, không chỉnh Canon firmware hoặc bootflag.
- Không cung cấp mã lỗi -1/-2/-3 của lần ASSERT trước: nhật ký lịch sử không đủ thông tin và bản này chủ động **không chạy Lossless**.

### Movie → QVFIL LJ Error Guide
- Hướng dẫn đọc ba nhánh lỗi **chỉ mang tính tham khảo**:
  - -1: encoder chưa sẵn sàng / thiếu tài nguyên;
  - -2: callback/encoder không kết thúc trong 1000 ms;
  - -3: JPEG lossless output marker không hợp lệ.
- Trạng thái trên màn hình **HIST: ?**; không phải telemetry thực tế.

### Tính năng giữ nguyên
- Sáu lựa chọn HUD v0.6.6, gồm **Cinema slim** và **Cinema clean**.
- Manual Focus Peaking gốc: `Overlay → Focus Peak`, sử dụng lens MF.
- `QVFIL Shoot Check`, `QVFIL Media Engine`, `QVFIL Recording Report`.
- **Toàn bộ `raw_video_rec_task()` và `compress_task()` giữ nguyên từng ký tự so với v0.6.6**, có kiểm thử đối chiếu tự động.
- Bảo vệ **BLOCK 5D3 Lossless** giữ nguyên. Không hỗ trợ 14-bit Lossless hay 3K.
- Source Magic Lantern ghim ở commit `ed3e7c0dfacfdeaf3349dee73edf9e3621217462`.

## Vì sao chưa sửa ngay lỗi ASSERT

Trong source 2025, `process_frame()` đưa slot `SLOT_CAPTURING` vào `writing_queue` trước khi `compress_task()` trả kết quả. Nếu bộ nén lỗi rồi chỉ đặt `buffer_full = 1`, phần flush ở `raw_video_rec_task()` vẫn có thể gặp slot chưa hoàn thành và kẹt/chạm ASSERT. Không được bỏ ASSERT rồi ghi frame lỗi vào MLV. V0.6.8 cố ý chỉ cung cấp preflight đọc trạng thái cho đến khi có một thiết kế và kiểm thử toàn diện hàng đợi/cleanup trên đúng nền tảng.

## Bản thử nghiệm và nghiệm thu có kiểm soát

Chỉ khi GitHub CI **PASS** và artifact MLV_LITE.MO có checksum:

1. Giữ **nguyên thẻ v0.6.6 đang chạy PASS**, không ghi đè, không format. Giữ bản sao toàn bộ SD/CF đã tạo. Kiểm tra khả năng đọc/checksum của bản sao trước khi cài module thử nghiệm.
2. Sử dụng **thẻ SD boot TEST khác** có môi trường Magic Lantern 5D3.123 tương thích, sao lưu `ML/MODULES/MLV_LITE.MO` cũ và chỉ thay module này trên thẻ TEST. Không cài lại Magic Lantern / chạy Firmware Update.
3. Trên máy, kiểm tra `Modules → mlv_lite.mo ON`; `Movie → QVFIL Cinema HUD` báo `v0.6.8`.
4. `Movie → QVFIL Lossless Diag` phải cho thấy `LJ OFF` khi RAW 10-bit không nén; `QVFIL LJ Error Guide` hiển thị `HIST: ?`. **Không chọn Lossless ON** để thử: bản chẩn đoán này không tự sửa lỗi.
5. `Cinema slim` và Focus Peak vẫn hoạt động như v0.6.6. Nếu cần, quay **RAW 10-bit uncompressed 1280×720 / 25p trong 5–10 giây**, dừng chủ động rồi kiểm tra file `.MLV` bằng MLV App. Không suy ra hardware PASS cho v0.6.8 nếu chưa thử trên máy.
6. Nếu treo, sai ký tự, lỗi MLV hay menu không đúng, tắt máy và khôi phục bằng thẻ v0.6.6 gốc.

## Trạng thái

- `V066_USER_HARDWARE_PASS`
- `FULL_CARD_BACKUP_OPERATOR_REPORTED`
- `BACKUP_RESTORE_NOT_INDEPENDENTLY_VERIFIED`
- `V067_SOURCE_ANALYSIS_PASS`
- `V068_READ_ONLY_DIAGNOSTIC_CREATED`
- `V068_NO_COMPRESSOR_OR_RAW_RECORDER_CHANGES`
- `V068_HARDWARE_TEST_PENDING`
- `LOSSLESS14_BLOCKED`

**Không phát hành bản này như một bản vá 14-bit Lossless.**
