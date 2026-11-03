# QVFIL v0.6.17 — ROM-Verified Color Preview Lab · 5D3.123

## Tình trạng nghiệm thu thực tế (ảnh IMG_5390.JPG / IMG_5391.JPG)

- `Cinema slim HUD → QVFIL v0.6.16`: xác nhận module đang hoạt động.
- `QVFIL ROM Check → ROM:672EEACE / SIG PASS`: ROM đã kiểm tra cho ra cùng tổng 32-bit với chữ ký `SIG_5D3_123=0x672EEACE` của pinned Magic Lantern 2025. Chỉ phạm vi đầu **256 KiB** vùng ROM tính từ `0xFF0C0000`, không xác thực toàn bộ firmware.
- `QVFIL ID Probe → M:5D3`, `FW:9.0.1 A6(3`: chuỗi `PROP_FIRMWARE_VER` khác nhãn firmware công khai `1.2.3` mà người dùng đã xác nhận trước đó. Chưa có nguyên nhân gốc về property string.
- Trong v0.6.16, `Color Lab` chưa được phép chạy vì `is_camera("5D3","1.2.3")` fail.
- `Draws:6 Gate:0` trên HUD Diagnostics **không phải** `F:N Xms` của Color Lab.

## Thay đổi duy nhất cho v0.6.17

- Điều kiện model/firmware của Color Lab không còn dùng trực tiếp `PROP_FIRMWARE_VER` đang có mismatch.
- Color Lab chấp nhận **đồng thời**:
  1. `is_camera("5D3", "*")` (đúng model đã biên dịch);
  2. `get_digic_version() == 5`;
  3. **Người dùng đã chủ động vào `Movie → QVFIL ROM Check`** và kiểm tra ROM hoàn tất trong phiên khởi động hiện tại;
  4. Chữ ký ROM bằng `0x672EEACE` đúng với ML 5D3.123;
  5. RAW bật / Movie LiveView / RAW recorder IDLE / LiveView x1 / kích thước RAW không vượt 1600×900 / Data Format 10-bit / sensor RAW source 14-bit.
- Chuyển hai biến cache ROM Check (chỉ là khai báo) lên trước macro Color Lab để callback Preview có thể đọc cache. **Không đọc ROM trong Preview loop**, không tốn chu kỳ quét ROM khi đang lia máy.
- `Color Lab` mặc định `OFF` ở mỗi lần khởi động, không được ghi cấu hình lưu.
- Menu giải thích rõ `RUN ROM CHECK` khi chưa xác thực, `ROM MISMATCH` khi chữ ký không đúng, `ARMED 0F` nếu điều kiện hợp lệ nhưng chưa dựng frame, và `F:N Xms` khi đã dựng được N lượt.
- `REC: BASE` trả Preview về đường Magic Lantern RAW gốc trong thời gian ghi.
- Giữ nguyên nguồn `raw_video_rec_task()`, `compress_task()`, `raw_rec_update_preview()` và I/O; không thay đổi mã hóa, luồng recorder, EDMA, buffer queue, hay dữ liệu MLV.
- Không thay đổi độ phóng của Canon Real-time hoặc thuật toán chuyển Bayer thành màu. Đừng xem đây là phiên bản đã chữa xong FPS.

## Nghiệm thu an toàn

1. Giữ nguyên thẻ known-good (v0.6.6 hoặc cấu hình ghi RAW đã PASS). Chỉ thay `ML/MODULES/MLV_LITE.MO` trên thẻ TEST đã có bản sao lưu. Không sửa `autoexec.bin`, Canon firmware, hay vùng ROM.
2. Khởi động, xem `Movie → Cinema slim HUD` hiển thị `QVFIL v0.6.17`. Nếu không, dừng.
3. `QVFIL Color Lab` phải `OFF / SAFE OFF` mặc định. Giữ RAW 1280×720, 10-bit uncompressed, 25fps, lens MF, Movie LiveView x1.
4. Chọn `Movie → QVFIL ROM Check`. Chỉ tiếp tục nếu hiện `ROM:672EEACE / SIG PASS`. Nếu `SIG FAIL` hoặc `TARGET FAIL`, dừng; không bật Lab.
5. Sang `Movie → QVFIL Color Lab`, chọn `Color STBY`. Nếu menu báo `RUN ROM CHECK`, phép ROM Check chưa được hoàn tất trong phiên này. Nếu `ROM MISMATCH`, dừng.
6. Thoát menu, để một cảnh tĩnh giàu màu ở STBY khoảng 5–10 giây; lia máy nhẹ hoặc xoay vòng nét một lần rồi trở lại tab Movie và chụp `QVFIL Color Lab`.
7. Các dấu hiệu: `ARMED 0F` = chưa có lượt vẽ thành công; `F:nnn xxms` = số lượt đã dựng + thời gian của lần cuối (KHÔNG PHẢI fps). Kiểm tra bằng mắt có bị thu nhỏ, chuyển xám, kéo đuôi, đông hình hay không.
8. **Chưa bấm REC** ở vòng này. Chỉ sau khi STBY ổn, và có nghiệm thu mới thực hiện thử 5–10 giây RAW trên thẻ TEST trong vòng sau.
9. Nếu màn hình lỗi, menu không phản hồi, hình bị giật/mất màu quá mức hoặc nhiệt độ bất thường: tắt Color Lab hoặc khởi động lại và thay lại module cũ. Lab tự OFF sau reboot.

## Định hướng hiệu năng / chẩn đoán

- Sau khi v0.6.17 thu được dữ liệu frame thực tế, phân tích thời gian `raw_preview_fast_ex()` và độ trễ UI trước khi thử lên v0.6.18.
- Canon Real-time là nguồn hiển thị màu mượt nhưng khung nhỏ; RAW preview thường khung lớn hơn nhưng chuyển màu nặng. Muốn vừa màu, vừa mượt, vừa lớn có thể phải dựng đường giám sát riêng; **không thể suy ra khả thi chỉ từ ảnh LCD**.
- Bảo toàn MLV đã ghi tốt quan trọng hơn chất lượng của tính năng Preview thử nghiệm.

**Trạng thái: ứng viên thử nghiệm, chỉ phát hành gói khi CI ARM/ELF/checksum PASS. Không tuyên bố camera PASS trước khi có ảnh thật.**
