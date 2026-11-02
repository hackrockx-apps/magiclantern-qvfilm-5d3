# QVFIL v0.6.1 — Fix menu Movie on Canon EOS 5D Mark III

## Kết quả nghiệm thu từ người vận hành v0.6.0 (2026-11-02)

- Máy đã cài QVFIL v0.6.0 và khởi động bình thường, vào Movie được.
- Người vận hành xác nhận quay trên **CF SanDisk Extreme 64GB UDMA7** hơn 20 giây và **chủ động bấm dừng**, không tự ngắt.
- File **`M02_1652.mlv`** được người vận hành mở trong **MLV App** và cho biết không có hiện tượng đứng khung. File MLV gốc không được đính kèm ở vòng này, nên ta chỉ đánh dấu **USER-REPORTED SHORT RECORDING PASS**, không khẳng định đã kiểm tra metadata, số frame bị bỏ hoặc ghi liên tục nhiều phút.
- Ảnh Movie cho thấy: `QVFIL Cinema HUD OFF`, `QVFIL v0.6.0`, **Gradual Exposure ON** (nên tắt khi làm bài thử định lượng).
- Menu **FAIL**: tên hai mục `QVFIL Storage Check`, `QVFIL Media Engine` hiển thị thành nhiều ký tự `A`; hai nhãn hiển thị `Draws:u`, `Obs:u.u`, cảnh báo `Observed u.u MiB/s`. Đây là lỗi định dạng hiển thị và/hoặc cách thư viện menu Canon xử lý chuỗi, chưa phải bằng chứng tốc độ thẻ bằng 0 hay bộ ghi RAW bị hỏng.

## Thay đổi trong v0.6.1

- Giữ mã nguồn gốc Magic Lantern 2025 `ed3e7c0dfacfdeaf3349dee73edf9e3621217462` và v0.6.0 passive telemetry nguyên trạng.
- Mã v0.6.0 dùng `MENU_SET_VALUE`/ `MENU_SET_RINFO` với `%u`, `%c` cho menu; snapshot thực tế trên 5D3 không render đúng các token này. Dùng **`%d` và `%s`**, cùng ép kiểu nguyên giới hạn đã kiểm soát để tránh khác biệt với Canon's non-standard `vsnprintf`. Không có phép ghi dữ liệu mới.
- Chủ động gọi `MENU_SET_NAME` trong bốn hàm update mục `QVFIL HUD Diagnostics`, `QVFIL Storage Check`, `QVFIL Media Engine`, `QVFIL Recording Report` để tên hiển thị được tạo rõ ràng sau khi core menu cấp phát vùng thông tin.
- Giá trị đích ghi hiện là chuỗi `CF` / `SD` thay vì ký tự ký hiệu `A`/`B` qua `%c` (phần xác định target vẫn dùng `get_cf_dcim_dir()`).
- Không thay đổi **một dòng nào** của hàm `raw_video_rec_task` so với v0.6.0 (có unit test so sánh nguyên vùng source), không sửa writer, codec, bit depth, tốc độ bus, storage driver, raw buffer, boot flags, menu Movie gốc hay blocker lossless 14-bit.
- Không giải quyết SD clock/SD overclock; nghiên cứu riêng.

## Các bước nghiệm thu

1. Sao lưu thẻ và **module v0.6.0** đang quay ổn trước khi làm gì. Giữ thẻ Magic Lantern nguyên bản và file ROM backup. Chỉ cài `MLV_LITE.MO` v0.6.1 khi exact-source unit tests và build ARM PASS, checksum SHA-256 được kiểm tra.
2. Gắn CF đã sao lưu dữ liệu. Khởi động, vào Movie; phiên bản phải báo `QVFIL v0.6.1`.
3. **Chưa cần quay**: kiểm tra ba mục `QVFIL Storage Check`, `QVFIL Media Engine`, `QVFIL Recording Report` có tên bình thường; các giá trị `Draws:0`, `Obs:...`, `Flow:...` là số thay vì `u.u`. Chụp ảnh Movie. Nếu vẫn có chữ `AAAA`, dừng việc thay module, quay lại v0.6.0 hoặc card gốc và lưu ảnh để truy sâu menu memory/ABI.
4. Tắt `Gradual Exposure` trong Movie để kiểm thử RAW có exposure nhất quán; đặt HUD OFF, FPS override OFF, RAW 1280×720/25p/10-bit uncompressed, Rec trigger OFF, Pre-record OFF.
5. Dùng `QVFIL Enter Cinema` để thoát menu, quay một clip 20–30 giây trên CF, chủ động dừng, đợi hoàn tất. Mở `QVFIL Recording Report` và `Media Engine`, ghi rõ `Flow`, `I/O`, `pending`, `Last stop`, rồi xem file mới bằng MLV App.
6. Khi qua bài ngắn, mới thử 1600×900 25p 10-bit rồi tăng thời lượng. Không thử 14-bit lossless hay SD Overclock trên card đang sử dụng để quay.
7. Nếu xảy ra lỗi ghi, tự ngắt, treo hoặc nội dung lỗi mới, khôi phục module v0.6.0 hoặc stock; bảo toàn file MLV và nhật ký.

## Trạng thái

`V060_CF_SHORT_MLV_USER_PASS`; `V060_MENU_FORMAT_FAIL`; `V061_SOURCE_ARM_PENDING` (cập nhật theo kết quả CI); `V061_HARDWARE_PENDING`; `LOSSLESS14_GUARDED`; `NO_SD_OVERCLOCK`.
