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


## Cảnh báo nghiệm thu trên máy — 03/11/2026: LIVEVIEW HOLD

Bản v0.6.8 đã được người dùng thử trên Canon EOS 5D Mark III firmware 1.2.3.

**Kết quả từng phần:**
- `Movie → QVFIL Lossless Diag`: hiển thị `LJ OFF`, 10-bit 1920×1080 — **UI PASS**.
- `Movie → QVFIL LJ Error Guide`: hiển thị `HIST: ?` — **UI PASS** (không phải lỗi compression mới).
- `Cinema slim` và Focus Peak đã có mặt.
- **LiveView NOT PASS:** người dùng quan sát hình gần trắng đen/ám xanh tím và cập nhật rất chậm. Ảnh điện thoại có histogram nhiều màu và một số điểm đỏ, chưa chứng minh file RAW mất màu.
- Người dùng quay 5–10 giây được nhưng **chưa cung cấp tệp .MLV** để chứng minh màu thực tế và số khung hình.

**Quan sát phụ:** HUD ghi `ISO220` trong khi thanh thông số gốc Magic Lantern/Canon phía dưới hiển thị `ISO A400D+`. Cần kiểm tra cách đọc Auto ISO từ `lens_info.iso` / `lens_info.iso_auto`; không được xem đây là số ISO đã đúng.

**Kết quả rà soát nguồn (upstream 2025 đã pin):**
- `RAW video → Preview` có `Auto / Real-time / Framing / Frozen LV`. `Framing` ghi rõ low-res, slow, not real-time. `Real-time` là LiveView màu, có thể framing không chuẩn ở một số chế độ.
- `raw_rec_update_preview` có nhánh `RAW_PREVIEW_GRAY_ULTRA_FAST` khi hàng đợi ghi lớn và khoảng ngủ preview 500/1000 ms để ưu tiên ghi; chưa biết có thực sự rơi vào nhánh này ở lần thử hay không.
- Patch v0.6.8 chỉ thêm các callback menu, không đổi `raw_rec_update_preview`, `compress_task` hoặc `raw_video_rec_task` theo kiểm tra mã nguồn. Chưa thể xác định đây là bug code v0.6.8 hay do cấu hình Preview/mode khác biệt.

**Quy trình đối chứng ngay, chỉ STBY, chưa quay thử tiếp:**
1. Giữ nguyên bản ghi và thẻ v0.6.8 làm bằng chứng, không flash/format.
2. Vào `Movie → RAW video → Preview` (mở submenu bằng SET/Q tùy giao diện) và chụp ảnh giá trị đang chọn.
3. Nếu đang chọn `Framing` hoặc `Frozen LV`, thử đổi sang `Real-time` chỉ trong STBY và kiểm tra tốc độ, màu. `Real-time` có thể framing sai ở crop/high-res, do đó không tự xem là phương án quay production. Có thể trở về `Auto` sau bài kiểm tra.
4. Nếu vẫn lỗi, tắt Focus Peak, rồi HUD (mỗi lần chỉ đổi một mục), kiểm tra không REC.
5. Trở về **thẻ boot v0.6.6 đã USER PASS** để so sánh cùng thông số. Không ghi đè thẻ v0.6.6.
6. Mở lại file .MLV đã ghi 5–10 giây trong MLV App để xác định màu dữ liệu, không suy diễn từ LCD.
7. Giữ `LOSSLESS14_BLOCKED` và không thử 3K. Không phát hành v0.6.8 làm bản stable khi LiveView chưa đạt.

**Hiện trạng:** `V068_DIAG_UI_USER_PASS` / `V068_LIVEVIEW_COLOR_PERFORMANCE_HOLD` / `V068_REAL_CAPTURE_COLOR_NOT_YET_VERIFIED` / `V066_LAST_KNOWN_GOOD` / `LOSSLESS14_BLOCKED`.
