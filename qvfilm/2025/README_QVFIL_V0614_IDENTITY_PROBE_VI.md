# QVFIL v0.6.14 – Camera Identity Probe (5D3.123)

## Kết quả nghiệm thu v0.6.13 từ IMG_5383.JPG (03/11/2026)

- `Cinema slim HUD → QVFIL v0.6.13`: đúng module đang chạy.
- `QVFIL Color Lab → Color STBY`: đã chọn.
- `ID 0/0 D5`: **cả hai kiểm tra `is_camera("5D3", "1.2.3")` (khởi tạo và thời điểm gọi) đều FALSE, DIGIC 5 TRUE**.
- Bộ dựng RAW Color Lab **không chạy**, không có `F:N Xms` hợp lệ.
- `Preview Guide → Frozen LV`: trạng thái Preview tại thời điểm chụp.
- `Draws:6 Gate:0` chỉ là HUD Diagnostics, không phải số lần Render của Color Lab.

**Không thay đổi firmware hay thử RAW trong khi nhận diện bị chặn.**

## Mã nguồn gốc được kiểm tra

Pinned Magic Lantern 2025 commit `ed3e7c0dfacfdeaf3349dee73edf9e3621217462`.

Trong `src/propvalues.c`, `is_camera(model,version)` so sánh:
- `__camera_model_short` (chuỗi compile-time `CAMERA_MODEL`) với model, và
- `firmware_version` (chuỗi cập nhật bởi `PROP_FIRMWARE_VER`) với firmware.

Vì `ID 0/0 D5` chỉ là kết quả gộp, nó không xác định được chuỗi nào khác. Có thể firmware property chưa sẵn sàng, phiên bản hiển thị khác, hoặc runtime core khác source được build. Không được suy ra firmware Canon thực sự bị sai.

## v0.6.14 thay đổi an toàn

- `Movie → QVFIL ID Probe`: item **chỉ đọc**, hiển thị `M:<model>` ở giá trị và `FW:<version>` ở cột bên phải; `EMPTY` khi trường chưa có dữ liệu.
- Chỉ sử dụng hai biến hiện có trong Magic Lantern: `__camera_model_short`, `firmware_version`. Không truy cập ROM, không đọc số serial, không lưu file, không thay đổi property.
- Độ dài UI bị giới hạn `M:%.6s` và `FW:%.10s` phù hợp LCD 5D3.
- Giữ nguyên `Color Lab` và hàng rào an toàn `get_digic_version()==5 && (cam_5d3_123 || is_camera("5D3","1.2.3"))`. Trạng thái `ID 0/0 D5` không được tự động mở khóa.
- Giữ nguyên toàn bộ `raw_rec_update_preview()`, `raw_video_rec_task()`, `compress_task()`, RAW writer, EDMAC, buffers, 14-bit lossless guard.
- Khi khởi động lại Lab vẫn `OFF`. Bản này **không tăng FPS hay phóng lớn LiveView**.

## Hướng dẫn nghiệm thu sau khi CI ARM PASS

1. Không ghi đè thẻ v0.6.6 đã PASS. Sao lưu và dùng thẻ TEST.
2. Lắp module QVFIL v0.6.14 **chỉ sau khi** CI PASS, kiểm tra SHA-256 file `MLV_LITE.MO`.
3. Bật máy và xem `Cinema slim HUD` phải ghi `QVFIL v0.6.14`.
4. **Giữ Color Lab = OFF**, chưa quay.
5. Vào `Movie → QVFIL ID Probe`, chụp toàn bộ dòng gồm `M:...` và `FW:...`.
6. Nếu model đọc `M:5D3`, FW rỗng → điều tra property `PROP_FIRMWARE_VER` và thời điểm cập nhật / tính tương thích core trước khi xử lý màu.
7. Nếu model không phải `5D3` → dừng vì có thể core/module mismatch; đối chiếu module với autoexec.bin, tránh cố ép.
8. Nếu cả hai đúng `5D3`/`1.2.3` nhưng `ID 0/0 D5` vẫn còn → kiểm tra timing, build/ABI và nội dung phép so; chưa mở khóa.
9. Nếu máy bị treo/overlay giật: tắt nguồn, quay lại thẻ known-good.

**Mục tiêu vòng nghiệm thu này là CHẨN ĐOÁN CHÍNH XÁC MODEL/FIRMWARE, không kiểm tra FPS.**
