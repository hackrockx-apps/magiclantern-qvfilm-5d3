# QVFIL v0.5.3 — Hướng dẫn thoát Transparent Menu trước khi quay

## Kết quả nghiệm thu v0.5.2
- Từ ảnh Canon 5D Mark III của người dùng: mục Movie hiển thị `QVFIL v0.5.2` / `Cinema overlay`; LiveView có hình nhưng dòng `REC indicator — Elapsed Time` và hướng dẫn `Press INFO (outside ML menu) to turn Canon displays off` vẫn hiện trên khung hình.
- Đây là bằng chứng **menu Magic Lantern còn được mở ở Transparent Menu**, chưa phải màn hình LiveView quay RAW độc lập. Không thể kết luận bộ ghi không hoạt động chỉ từ ảnh này.
- Trong đúng source `src/menu.c` commit `ed3e7c0df`, ở handler `handle_ml_menu_keys()`: khi menu đang mở, `BGMT_LV` đổi `menu_lv_transparent_mode`, **không đóng menu**.
- Trong source `modules/raw_video/mlv_lite/mlv_lite.c` cùng commit: `raw_rec_keypress_cbr()` bỏ qua phím ghi nếu `!liveview_display_idle() && !RECORDING_RAW`. Nút REC được xử lý qua `MODULE_KEY_LV || MODULE_KEY_REC` **sau khi menu thoát**.
- Trong code QVFIL v0.5.2, `qvfilm_draw_cinema_overlay()` chỉ vẽ khi `!gui_menu_shown() && liveview_display_idle()`; do đó menu đang trong suốt khiến overlay không hiện là đúng điều kiện tự bảo vệ.

## Sửa v0.5.3 (không thay cơ chế nút ghi)
- Đổi nhãn menu dài `QVFIL Cinema HUD` thành **`QVFIL HUD`**, tùy chọn rút gọn **`OFF / Bars / Cinema`** để không chồng chữ trong LCD.
- Trạng thái `Cinema` hiển thị cảnh báo hướng dẫn **`Exit ML menu with DELETE/MENU before using START/STOP.`**. Mục giúp nhắc riêng rằng nhấn LiveView khi đang trong ML menu chỉ chuyển Transparent Mode, không quay.
- Giữ nguyên 10-bit RAW, hiển thị BPP thực tế, cơ chế stop/start gốc, lossless fail-closed từ v0.5.1. **Chưa khắc phục nén 14-bit lossless**.
- Không sửa `BGMT_LV`, `BGMT_REC`, phím Shutter, firmware Canon hay nút điều khiển RAW của ML. Không tự thoát menu bằng callback.

## Bài thử khuyến nghị ngay, không cần cập nhật module
1. Trên **v0.5.2 hiện tại**, vào Movie: RAW Video ON, QVFIL HUD Cinema overlay, Gradual Exposure OFF, Data format 10-bit uncompressed, Rec trigger OFF, Global Draw ON.
2. Bấm **DELETE (thùng rác)** để đóng hoàn toàn Magic Lantern menu. Nếu máy còn ở menu trong suốt, nhấn **MENU** một lần để thoát chế độ trong suốt, tiếp tục MENU hoặc DELETE để đóng menu hẳn. Đừng dùng nút LV khi menu đang mở.
3. Gạt công tắc quanh START/STOP sang camera quay video; nếu LiveView chưa mở, mở LiveView sau khi ML menu đã đóng. Nhấn INFO để ẩn lớp thông tin Canon; tránh bấm lại Q/Menu.
4. Xác nhận trên LCD chỉ có hình LiveView và không còn dòng được bôi xanh `REC indicator` hay cảnh báo `Press INFO outside ML menu`.
5. Chờ một giây, kiểm tra HUD `STBY` (vẽ khi Global Draw hoạt động). Bấm START/STOP để ghi RAW 3–5s; nhận biết `REC` và xác nhận file .MLV mới giải mã được sau khi dừng.
6. Nếu lại trở về Movie menu mà không ghi, chụp ảnh **toàn bộ LCD trước khi bấm**, kiểm tra mode lever và trạng thái menu/Modules; báo lại. **Không** lặp nhấn nhiều lần, không thử lossless, không flash firmware.

## Trạng thái
- `v0.5.2_INSTALLED_AND_MENU_VISIBLE_PASS`
- `MOVIE_MENU_TRANSPARENT_MODE_OBSERVED`
- `MLV_REC_TRIGGER_NOT_YET_VALIDATED_WITH_MENU_CLOSED`
- `v0.5.3_SOURCE_USABILITY_FIX_BUILD_PENDING`
