# QVFIL v0.6.13 – Camera identity gate fix (5D3.123)

## Nghiệm thu 03/11/2026

Từ sáu ảnh user gửi:
- Module Movie menu hiển thị **QVFIL v0.6.12**, chứng minh bản mới đã được nạp (khắc phục nhầm version v0.6.10 trước đó).
- Đã chọn `QVFIL Color Lab → Color STBY` nhưng tình trạng **`5D3.123 ONLY`**: Color Lab đang FAIL tại hàng rào nhận diện 5D3.123, chưa xác nhận có lượt dựng màu nào hoàn thành.
- `QVFIL Preview Guide → Frozen LV` ở ảnh cuối. `Draws:73 Gate:0` thuộc HUD Diagnostics, **không phải** bộ đếm F:N của Lab.
- `RAW video ON 1280×720 10b`, 25p; 1.50x trên dòng RAW video là hệ số khung/crop, không tự chứng minh LiveView x1 hay x5.
- Ảnh LiveView có hình màu, có các vùng xem lớn/nhỏ và tính chất màu khác nhau, nhưng không chứng minh FPS, tốc độ REC hoặc rằng Lab đã chạy.
- Nhiệt độ đọc từ LCD khoảng 32–37°C tại các thời điểm chụp, không đủ để suy luận thermal benchmark.
- User từng xác nhận máy chạy Canon firmware công khai 1.2.3 và file MLV trước đó mở được bằng MLV App. **Chưa có MLV ghi bằng v0.6.12 được cung cấp để xác minh độc lập.**

## Nguyên nhân kỹ thuật được nhận diện

Tại mã nguồn ML upstream 2025 pin `ed3e7c0dfacfdeaf3349dee73edf9e3621217462`:
`is_camera("5D3", "1.2.3")` so sánh `__camera_model_short` với model và giá trị `firmware_version` đang được property handler cập nhật. MLV Lite đã gọi cùng hàm trong `raw_rec_init()` và lưu vào `cam_5d3_123`. Trong v0.6.12, macro Color Lab tiếp tục gọi `is_camera` động và bị chặn như ảnh.

Ảnh **chưa đủ để biết vì sao runtime version string khác với giá trị dự kiến**, hoặc biến `cam_5d3_123` được cache có giá trị gì. Không được xóa điều kiện target 5D3.123 để ép tính năng chạy.

## v0.6.13 thay đổi

- `QVFIL_LAB_CAMERA_OK` dùng `(cam_5d3_123 || is_camera("5D3","1.2.3")) && get_digic_version() == 5`. Biến cached được chính `raw_rec_init()` của upstream gán từ kiểm tra **đúng model+firmware** vào lúc module khởi tạo. Không chấp nhận firmware 1.1.3, model khác hoặc DIGIC khác.
- Nếu cả cached/live đều fail, dòng trạng thái thay `5D3.123 ONLY` bằng `ID <cached>/<live> D<digic>`. Ví dụ `ID 0/0 D5` chứng minh cả 2 nhận diện đều thất bại, **Lab vẫn khóa**.
- Nếu cached thành công nhưng live thất bại, Lab được phép tiếp tục kiểm tra các điều kiện khác, không tự động cưỡng bức buffer.
- Giữ `SAFE OFF`, `ARMED 0F`, `F:N Xms`, các thông báo khắc phục khác, `Color STBY` tự OFF sau khi reboot.
- Không thay đổi `raw_preview_fast_ex` hay thuật toán RAW Color Halfres, kích thước Canon Real-time, nhịp cập nhật, `raw_video_rec_task`, `compress_task`, DMA, FIO, 14-bit Lossless.
- Vì vậy đây là **bug fix camera gate**, **không phải** bản tăng FPS/fullscreen.

## Kiểm tra trước nghiệm thu

CI phải: lấy đúng ML2025 commit, pass toàn bộ hồi quy, xác minh recorder và compressor byte-identical, biên dịch core và `MLV_LITE.MO` cho 5D3.123, xác thực ARM ELF và xuất checksum. Chỉ sau đó module mới được xem là review candidate.

## Quy trình nghiệm thu an toàn

1. Giữ nguyên thẻ known-good v0.6.6, không động đến Canon firmware hoặc autoexec.bin. Dùng thẻ TEST đã sao lưu.
2. Kiểm checksum `MLV_LITE.MO` và boot: `Movie → Cinema slim HUD` phải hiển thị **QVFIL v0.6.13**, nếu không, dừng.
3. RAW 1280×720, 10-bit uncompressed, 25p; LiveView Movie x1; tắt thử 14-bit Lossless và không overclock.
4. Vào tab Movie, `QVFIL Color Lab` chọn `Color STBY`; mở LiveView STBY vài giây rồi quay về menu.
5. Nếu hiện `ID 0/0 D5` hoặc `ID 0/0 D?`: dừng, chụp màn hình, **không cố bypass**. Điều này cho thấy cached ID cũng không được hệ thống xác nhận; cần tìm nguồn phiên bản firmware thực tế.
6. Nếu `ARMED 0F`: chỉ đủ điều kiện nhưng chưa có frame đã hoàn tất. Chụp ảnh và không coi là PASS.
7. Nếu `F:N Xms`: đã hoàn tất N lượt, mất X ms gần nhất. So sánh với phản hồi khi xoay focus và lia máy; không suy ra FPS từ số này.
8. Nếu bất thường, mất màu, giật nặng, nóng nhanh hoặc menu lỗi: tắt Color Lab về OFF hoặc khởi động lại.
9. Chưa quay thử đến khi STBY ổn và anh đã báo status; sau đó mới kiểm tra MLV 5–10 giây trên thẻ TEST nếu cần.

**Trạng thái:** v0.6.12 module boot confirmed, Lab gate failed; v0.6.13 source patch pending CI/hardware acceptance. Lossless14 blocked.
