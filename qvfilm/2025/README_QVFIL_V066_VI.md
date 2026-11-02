# QVFIL v0.6.6 – Cinema Slim HUD (Canon EOS 5D Mark III / firmware 1.2.3)

## Kết quả nghiệm thu (02/11/2026)
- **QVFIL v0.6.6 Cinema Slim: USER HARDWARE PASS** — người dùng đã hoàn tất nghiệm thu trên Canon EOS 5D Mark III và xác nhận PASS.
- Chưa ghi nhận chi tiết thời lượng/độ phân giải/bit-depth của bài test v0.6.6 trong xác nhận này; không tự suy diễn rằng đã thực hiện bài stress test dài hoặc kiểm tra độc lập từng frame.
- QVFIL v0.6.5 menu `Movie > QVFIL Cinema HUD > Cinema clean` hoạt động, bốn thông số hình ảnh: 105mm / f4.0 / 1/33 / ISO3200 ở hai hàng và histogram bên phải không bị che.
- Người vận hành xác nhận **Focus Peak hoạt động** và quay RAW **10 giây** ở cấu hình thực tế ổn định. Chưa có file MLV gửi để phân tích toàn vẹn khung hình độc lập; không tuyên bố zero drops dựa trên ảnh LCD.
- Thanh thông số Canon/ML dưới cùng còn hiển thị song song với HUD; panel 2x2 v0.6.5 (490x70 pixels) và panel phụ phía trên (330x26) chiếm nhiều diện tích màn hình.
- V0.6.4 đã được nghiệm thu Large cinema hiển thị khi REC không nhấp nháy; v0.6.3 đã có 1920x1080 RAW 4 phút MLV user PASS.
- **Giữ v0.6.5 làm mốc khôi phục an toàn.**

## Nâng cấp v0.6.6
- Giữ nguyên 5 chế độ HUD v0.6.5 theo đúng index: OFF, Info bars, Cinema overlay, Large cinema, Cinema clean.
- **Thêm lựa chọn thứ sáu, opt-in: Cinema slim.** Thay vì 2x2 FONT_LARGE, nó sử dụng một dải chữ FONT_MED ở phần dưới bên trái với 4 giá trị: focal length / aperture / shutter reciprocal / ISO. Không vẽ lại banner QVFIL STBY phía trên, vì core ML đã hiển thị RAW/FPS/REC.
- Bản bitmap 720x480: `bmp_fill(COLOR_ALMOST_BLACK,35,352,526,30)`, các tọa độ chữ (42,356), (179,356), (312,356), (420,356). Dải nằm bên trái histogram (trong ảnh của người dùng); thực tế vẫn cần kiểm chứng trên máy vì bố cục Overlay tùy thiết lập.
- Diện tích nền mới: `526x30=15,780 px` so với `490x70+330x26=42,880 px` của mode Cinema clean, tức giảm ~63% phần bitmap nền do QVFIL tạo trong chế độ đó. Đây là số liệu kích thước vùng vẽ, **không phải đo đạc màn hình/hệ thống**.
- Text FONT_MED sẽ nhỏ hơn mode Cinema clean: anh có thể quay lại mode cũ khi cần chữ lớn.
- Mọi chỉ số vẫn lấy từ lens_info / RAW module như trước. Không thêm thuật toán Focus Peaking, không tăng tốc độ vẽ; khi REC liên tục giữ cơ chế không vẽ lại từng khung để giảm nhấp nháy.
- Tiếp tục dùng `Magic Lantern > Overlay > Focus Peak` và `Global Draw`, ở MF. V0.6.5 Focus Peak USER PASS giữ nguyên.
- **raw_video_rec_task** không thay đổi so với v0.6.5; không đổi sensor, buffer, writer, cấu hình lossless, SD/CF clock, bootflag hay firmware. Chế độ 14-bit lossless từng gây ASSERT vẫn được chặn.
- Pinned Magic Lantern source: `ed3e7c0dfacfdeaf3349dee73edf9e3621217462`.

## Trạng thái nghiệm thu
- `V066_EXACT_SOURCE_TEST_PASS`
- `V066_ARM_BUILD_PASS`
- `V066_USER_HARDWARE_PASS` — confirmation received after the test checklist.
- `V066_CAMERA_TEST_DETAILS_NOT_RECORDED` — ask for exact mode/duration only if needed for future stress-test matrix.
- `V066_RAW_RECORDER_UNCHANGED_BY_SOURCE_TEST`
- `LOSSLESS14_BLOCKED`

## Bảo toàn hệ thống
- Giữ thẻ và cấu hình v0.6.6 đã PASS nguyên trạng làm mốc làm việc hiện tại; không thử lossless14/3K hoặc thay bootflag/firmware/clock.
- Trước khi chuẩn bị bất kỳ module cài mới nào, hoàn tất xác minh độc lập firmware công khai Canon, audit đọc-thẻ và backup/recovery review theo readiness gate hiện hành.

## Checklist nghiệm thu ban đầu (tham chiếu, không yêu cầu chạy lại)
1. Không chép đè lên thẻ khởi động v0.6.5 đang hoạt động; sao lưu thẻ CF, SD, ROM gốc. Dùng thẻ SD boot **TEST riêng** và CF test.
2. Tải artifact có tên **QVFIL_v0.6.6_EXPERIMENTAL_MODULE_5D3_123_UNTESTED** trong GitHub Actions mới nhất của nhánh v0.6.6. Giải nén, kiểm tra `SHA256SUMS.txt` đối với module, sau đó chỉ sao chép `MLV_LITE.MO` vào `ML/MODULES/` của thẻ boot TEST. Không flash Canon firmware, không sửa bootflag, không overclock.
3. Trong `Modules`, xác nhận `mlv_lite.mo` ON; trong tab Movie xác nhận v0.6.6 và đầy đủ `RAW video`, `Shoot Check`, `Media Engine`, `Recording Report`.
4. Vào `Movie > QVFIL Cinema HUD > Cinema slim`, `QVFIL Enter Cinema` sang LiveView. Chụp ảnh STBY; xác nhận **chỉ một dải 4 thông số**, không còn banner QVFIL phụ phía trên, và dải không che histogram hay phần dưới gốc. Trong ảnh trước đó 105mm/f4.0/1/33/ISO3200 là giá trị test chứ không phải cố định.
5. Bật `Overlay > Focus Peak` đã dùng được, ống kính MF, thử quay vòng nét và theo dõi vùng nét. Nếu hình ảnh khó quan sát hơn do chữ nhỏ, chọn lại `Cinema clean`.
6. Test RAW ngắn **1280x720, 25p, 10-bit uncompressed** trên CF test: quay 5–10s, STOP thủ công, mở .MLV trong MLV App. Kiểm tra không tự ngắt, không chớp hình. Chỉ sau khi PASS mới thử các độ phân giải, bit depth và thời lượng **đã hoạt động ổn ở v0.6.5**.
7. Nếu treo máy, lỗi ký tự, menu mất hoặc .MLV không thể mở: tắt và quay lại thẻ v0.6.5 nguyên trạng. Không thử lossless/3K cho đợt này.

## Trạng thái hiện hành
V065_CINEMA_CLEAN_USER_PASS
V065_FOCUS_PEAK_USER_PASS
V066_CINEMA_SLIM_USER_HARDWARE_PASS
V066_EXACT_SOURCE_TEST_PASS
V066_ARM_BUILD_PASS
V066_RAW_RECORDER_UNCHANGED_BY_SOURCE_TEST
LOSSLESS14_BLOCKED
