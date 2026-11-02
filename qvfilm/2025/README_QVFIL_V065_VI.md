# QVFIL v0.6.5 — Cinema Clean HUD + Focus Peak (Canon 5D3.123)

## Nghiệm thu người dùng v0.6.4 (02/11/2026)
- Operator xác nhận **Large Cinema HUD ổn định khi quay RAW, không nhấp nháy**, ảnh REC cho thấy RAW / 25.000 FPS / 35°C / REC 00:06. 00:06 là thời điểm chụp ảnh, **không phải** tổng thời lượng video hay bằng chứng kiểm tra toàn file.
- Sau khi gạt ống kính sang **MF**, người dùng đã tìm được `Focus Peak` đúng chỗ và xác nhận **hoạt động hoàn hảo**.
- Đường dẫn đúng: **Magic Lantern → Overlay → Global Draw / Focus Peak**. Tab `Focus` có Trap Focus / Follow Focus / Focus Settings nhưng **không chứa Focus Peak**. v0.6.3/v0.6.4 có câu trợ giúp sai vị trí; v0.6.5 sửa lỗi hướng dẫn.
- Hiển thị HUD cũ chiếm một dải rộng gần góc dưới bên phải, hơi gần histogram. Giao diện mới phải giữ nguyên v0.6.4 đã hoạt động, không phá các chế độ đã lưu.
- Trước đó v0.6.3 đã được người dùng xác nhận RAW 1920x1080 / 4 phút, MLV phát bình thường; v0.6.2 đã xác nhận RAW 1600x900 / 3 phút. **Không tuyên bố không drop frame độc lập** nếu chưa nhận được file nguồn.
- `QVFIL Shoot Check` đã được build ở v0.6.4 nhưng chưa có dữ liệu nghiệm thu menu thực tế.

## Điểm mới trong mã nguồn v0.6.5
- Thêm **lựa chọn thứ năm**, chỉ khi người dùng tự chọn: `Movie → QVFIL Cinema HUD → Cinema clean` (mode 4). Các mode 0-3, trong đó `Large cinema` (3), giữ nguyên thứ tự và giá trị cấu hình.
- Cinema clean chia **4 giá trị chữ lớn thành bố cục 2×2 ở phía dưới bên trái** (tiêu cự / khẩu độ, tốc độ màn trập / ISO); vẽ panel màu đen từ BMP x=35, y=312, width=490, height=70. Góc phải dành chỗ cho histogram; thanh thông tin gốc dưới cùng không bị thay đổi. Vị trí thực tế **phải nghiệm thu trên máy thật**.
- Giữ panel `QVFIL STBY/REC FPS` nhỏ tại x34 y105. Vẫn dùng **duy nhất callback bitmap đã có**; khi RAW REC liên tục thì không vẽ lại HUD QVFIL (số có thể tạm thời đóng băng). Không thêm phát hiện focus, xử lý pixel, FIO hay callback mới.
- Sửa hướng dẫn `QVFIL Focus Assist`: `Overlay > Global Draw`, `Overlay > Focus Peak`, gạt lens sang MF, chỉnh Threshold. Không giả định màu Red luôn có hoặc tự bật Focus Peak.
- V0.6.4 `Shoot Check`, `Media Engine`, `Recording Report` và phép tính ước lượng CF vẫn giữ nguyên. Không biến ước tính I/O thành cam kết.
- Bất biến nghiêm ngặt `raw_video_rec_task` so với v0.6.4, không chạm RAW writer, bộ đệm, overclock, encoder, bootflag, Canon firmware. Lossless/14-bit nén vẫn bị chặn để tránh ASSERT cũ.
- Source lock: `ed3e7c0dfacfdeaf3349dee73edf9e3621217462` của Magic Lantern 2025.

## Nghiệm thu v0.6.5 trên **thẻ TEST RIÊNG**

1. **Không thay đổi thẻ SD/CF v0.6.4 đang hoạt động**, giữ backup ROM trước đây. Chỉ dùng thẻ boot thử nghiệm 5D3.123 đã chuẩn bị; kiểm tra checksum file MLV_LITE.MO tải từ GitHub Actions v0.6.5 sau khi CI/ARM PASS. Không flash máy hoặc đổi bootflag.
2. Nạp module vào thẻ test /ML/MODULES/, khởi động lại. Tab Modules xác nhận `mlv_lite.mo ON`. Tab Movie xác nhận `RAW video ON`, `QVFIL Cinema HUD v0.6.5`, các mục Shoot Check / Media Engine / Recording Report đầy đủ.
3. Vào `Movie → QVFIL Cinema HUD` chọn `Cinema clean`. Bật `Overlay → Global Draw` và `Overlay → Focus Peak` như cấu hình người dùng đã nghiệm thu. Gạt MF; chọn `QVFIL Enter Cinema` để thoát menu.
4. Chụp ảnh HUD ở STBY; so sánh thông số tiêu cự, khẩu, shutter, ISO với thanh Canon dưới; kiểm tra bố cục 2×2, tránh histogram và phần thông tin gốc. Di chuyển vòng nét kiểm tra peaking trên chủ thể; nếu quá rối thì tắt histogram hoặc thử mode Large cinema cũ.
5. Test RAW **1280×720 / 25fps / 10-bit uncompressed** 5–10 giây bằng thẻ CF test, dừng chủ động, kiểm tra file .MLV trong MLV App. Trong khi REC quan sát màn hình có ổn định không; số HDR có thể giữ giá trị ban đầu, đây là cơ chế chống nhấp nháy.
6. Nếu ổn mới thử mức 1920×1080 / 25fps / bit depth **đã dùng thành công** ở v0.6.4 (không tự tăng mức nén hoặc dữ liệu) 30 giây rồi tối đa 4 phút; kiểm tra MLV và dấu hiệu drop frame.
7. Nếu bất kỳ lỗi menu, treo máy, màn hình chớp hoặc file .MLV lỗi: **tắt máy, quay lại thẻ boot v0.6.4 còn nguyên**. Không thử 14-bit lossless hoặc 3K trong đợt này.

### Kết quả được phép ghi nhận
- `V064_HUD_REC_USER_PASS_NO_FLICKER`
- `V064_NATIVE_FOCUS_PEAK_USER_PASS`
- `V065_SOURCE_ARM_BUILD_PENDING` (khi viết tài liệu; xem GitHub Actions mới nhất)
- `V065_HARDWARE_ACCEPTANCE_PENDING`
- `V065_NO_RECORDER_CHANGE`
