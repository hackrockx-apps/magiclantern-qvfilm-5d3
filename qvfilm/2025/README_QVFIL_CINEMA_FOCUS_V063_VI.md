# QVFIL Cinema Monitor v0.6.3 — Canon EOS 5D Mark III / 5D3.123

## Hardware checkpoint: 02/11/2026 — cập nhật sau nghiệm thu v0.6.2

### Bằng chứng người dùng đã xác nhận
- Đã quay RAW ở độ phân giải **1600×900 trong 3 phút**, chủ động dừng, không bị máy tự ngắt.
- Người vận hành đã kiểm tra **file .MLV** của lần quay và báo hình ảnh rất ổn.
- Bản v0.6.2 không còn lỗi ký tự hiển thị trong các mục đang quan sát trên Movie.
- Đây là **USER HARDWARE PASS — 1600×900 / 3 phút / mở được MLV**, không còn là “RAW chưa xác nhận”. Đây vẫn **chưa phải phân tích độc lập từng frame**: chưa có chính file .MLV, dữ liệu dropped frames hay full-decode report được tải lên.
- v0.6.0 trước đó đã quay CF >20 giây, mở được `M02_1652.mlv` bằng MLV App; v0.6.1 đã được người dùng xác nhận nhãn menu hợp lệ.

### Hai ảnh LCD mới — đừng suy diễn lỗi module chỉ từ khung hình
- Ảnh Movie hiện chỉ hiển thị từ **Gradual Exposure** đến **Movie Tweaks**. Không thấy `RAW video` và menu QVFIL **trong vùng ảnh**, nhưng chưa biết chúng có nằm ở phần menu khác/trên-dưới trang hoặc bị ẩn bởi chế độ hiển thị Magic Lantern hay không. **Không kết luận module `mlv_lite.mo` chưa nạp chỉ từ hai ảnh**.
- Ảnh LiveView có overlay Magic Lantern và hiện **105mm, f/4.0, 1/33, ISO 3200D+, 5500K, 25.000 fps, 31°C**, kèm tên hiển thị **MVI_8996**. Chỉ riêng tên MVI không thể thay thế bằng chứng đầu ra; ngược lại nó cũng **không phủ định** báo cáo thực tế đã tạo và kiểm tra được file .MLV.
- Chú ý góc dưới có chữ **AF** ở thời điểm chụp; muốn thử Manual Focus Peak nên chuyển công tắc ống kính sang MF.
- Tránh gán các ảnh này là UI của v0.6.3: đây là ảnh nghiệm thu **v0.6.2**.

## Checkpoint menu Movie trước khi thử v0.6.3 — không thay đổi chức năng quay đang PASS

1. Giữ nguyên thẻ có bản v0.6.2 đang hoạt động, sao lưu nguyên trạng; **không chép đè module trên thẻ này**.
2. Mở Magic Lantern → Movie → dùng bánh xe/joystick duyệt hết mục trên và dưới vùng đang hiển thị. Thử chuyển chế độ hiển thị menu Magic Lantern theo hướng dẫn tại máy (nút MENU khi đang trong menu ML, nếu có), rồi quan sát xem các mục ẩn hiện ra hay không; không thay đổi cài đặt RAW trong bước này.
3. Kiểm tra `Modules → mlv_lite.mo` có ON hay không; nếu ON và vừa tạo thành công .MLV ở lần quay đó, không vội tắt/bật hoặc thay module. Ghi lại phiên bản / cảnh báo module nếu có.
4. Tìm các mục: `RAW video`, `QVFIL Cinema HUD`, `QVFIL Media Engine`, `QVFIL Recording Report`. Nếu mất mục tùy biến QVFIL nhưng `.MLV` vẫn được tạo, kiểm tra xem module đang nạp là bản stock hay QVFIL, menu ẩn, hoặc thẻ boot SD/CF khác với bản dùng để quay.
5. Nếu có thể, chụp riêng **Modules** và Movie sau khi duyệt từ đầu đến cuối. Không cần quay lại 3 phút chỉ để chứng minh file MLV: kết quả này đã được người dùng nghiệm thu.

## Thay đổi trong mã nguồn v0.6.3 (chưa nghiệm thu bằng máy thật)

- Bổ sung lựa chọn thứ tư `Movie → QVFIL Cinema HUD → Large cinema`; ba lựa chọn trước **OFF / Info bars / Cinema overlay** được giữ nguyên.
- Hiển thị cỡ chữ **FONT_LARGE** cho các giá trị từ API máy ảnh: tiêu cự `lens_info.focal_len` (mm), khẩu độ `lens_info.aperture` (f-stop x10), tốc độ `get_current_shutter_reciprocal_x1000` và ISO `lens_info.iso` / `lens_info.iso_auto`. Thiếu thông tin sẽ hiển thị `--` thay vì số giả.
- Overlay lớn ở phía dưới khung; panel `STBY/REC + FPS` riêng. Lưu ý chưa kiểm tra vị trí thật trên LCD, có thể trùng phần thông số gốc của Magic Lantern.
- Giữ cách vẽ low-flicker: **không vẽ lại liên tục trong lúc RAW REC**; thông số có thể tạm giữ giá trị cũ khi đang quay.
- `Movie → QVFIL Focus Assist` **chỉ là hướng dẫn read-only** để bật **Focus → Focus Peak** của ML core (màu Red, Threshold) cùng Magic Zoom (nếu có). Không phải thuật toán peaking mới kiểu Blackmagic; không xử lý ảnh toàn khung liên tục, không tự điều khiển focus.
- Giữ nguyên `raw_video_rec_task` so với v0.6.2; không can thiệp writer I/O, RAW codec, firmware, bootflag, SD overclock.
- Lỗi `14-bit lossless` của 5D3.123 vẫn **bị chặn** vì ASSERT trước đây; không kiểm nghiệm 3K/lossless ở bước này.

## CI và artifact đã tồn tại
- Source-lock Magic Lantern 2025: `ed3e7c0dfacfdeaf3349dee73edf9e3621217462`.
- ARM CI **PASS** tại https://github.com/hackrockx-apps/magiclantern-qvfilm-5d3/actions/runs/41442715193 (commit `8031c4ddb1fb9ef67e6a33230d451c4b5074f7f7`, trước cập nhật tài liệu này).
- Artifact **QVFIL_v0.6.3_EXPERIMENTAL_MODULE_5D3_123_UNTESTED**: `MLV_LITE.MO`, `SHA256SUMS.txt`, cảnh báo chưa thử trên máy; hết hạn 16/11/2026 theo GitHub. Artifact chỉ là bản biên dịch, **KHÔNG phải bản đã nghiệm thu v0.6.3**.

## Nghiệm thu v0.6.3 trên thẻ TEST RIÊNG (sau khi xác minh menu)
1. Bảo toàn thẻ SD đang ghi RAW v0.6.2 ổn định và bản ROM backup; dùng thẻ boot thử nghiệm đã backup riêng với firmware 5D3.123. Chỉ thay `ML/MODULES/MLV_LITE.MO` trên thẻ test, kiểm tra hash.
2. Boot máy và xác nhận module v0.6.3 thực sự nạp; Movie có `RAW video`, `QVFIL Cinema HUD`, `QVFIL Focus Assist`, `QVFIL Media Engine`, `QVFIL Recording Report`.
3. Chọn `Large cinema` và `Global Draw ON`; kiểm tra chữ lớn khi STBY, đổi tiêu cự/khẩu/ISO và so với giá trị Canon. Xem có chồng phần hiển thị khác hay tràn màn hình không.
4. Chuyển ống kính sang MF, bật `Focus → Focus Peak`, chọn màu Red, chỉnh Threshold với vật nhiều cạnh rõ nét và thử Magic Zoom. Quan sát peaking khi STBY và khi REC; hiệu quả có thể bị giảm do gating core lúc ghi RAW.
5. Test RAW **1280×720 / 25p / 10-bit uncompressed**, FPS override OFF, Gradual Exposure OFF, pre-record OFF; quay 5–10 giây và kiểm tra file .MLV trên CF trong MLV App. Sau khi đạt mới mở rộng 20–30 giây, rồi 1600×900 / 3 phút trên thẻ test.
6. Khi có lỗi load, treo máy, nhấp nháy nặng, rớt khung hoặc thiếu .MLV, dừng nghiệm thu; tháo thẻ test và trở lại thẻ v0.6.2 đã PASS. **Không flash Canon, không thay bootflag, không overclock.**

## Trạng thái chính xác
- `V062_1600x900_3MIN_USER_MLV_PASS`
- `V062_FULL_FRAME_INTEGRITY_NOT_INDEPENDENTLY_ANALYZED`
- `V062_MENU_QVFIL_VISIBILITY_UNRESOLVED`
- `V063_EXACT_SOURCE_ARM_CI_PASS`
- `V063_EXPERIMENTAL_MODULE_AVAILABLE`
- `V063_CAMERA_HARDWARE_PENDING`
- `NO_OVERCLOCK`, `LOSSLESS14_BLOCKED`
