# QVFIL v0.6.9 – Preview Guide & Cinema Slim Auto ISO

**Canon EOS 5D Mark III | Canon firmware 1.2.3 | Magic Lantern 5D3.123 | upstream 2025 SHA ed3e7c0dfacfdeaf3349dee73edf9e3621217462**

## Vì sao có bản 0.6.9

Ngày 03/11/2026, người vận hành nghiệm thu v0.6.8: ở RAW 1280×720 / 10-bit / 25fps, `Preview Auto` hiển thị ám màu (xanh/tím, gần trắng đen), chậm; khi chuyển sang `Real-time` LiveView có màu nhưng vùng hình chỉ ở giữa, có viền đen rộng. Người vận hành quay khoảng 17 giây và xác nhận mở `.MLV` bằng MLV App **hình ảnh tốt**. Ảnh khi đang REC chụp đúng thời điểm màn hình hiện `00:08`, không phải báo cáo cả 17 giây. Không có file .MLV đính kèm để đọc frame-level drop/timestamps độc lập.

Theo pinned source, RAW > Preview có `Auto / Real-time / Framing / Frozen LV`; Framing dùng đường raw_preview_fast_ex có thể chậm/low-res; Real-time sử dụng Canon LV, có thể không đúng khung crop. Auto là một chính sách theo res/fps/framing, không thể suy ra chắc chắn đã chọn đường nào từ tên hiển thị. Vì v0.6.8 patch chỉ thêm menu callbacks, không thay đổi preview code, **chưa có chứng cứ xác định đây là regression code** cho đến khi A/B với v0.6.6 cùng setting.

Ảnh v0.6.8 còn cho thấy HUD QVFIL `ISO560` trong khi thanh Magic Lantern gốc `ISO A800D+` (Auto ISO và Highlight Tone Priority); đây không phải giá trị ISO thủ công tương đương. Mục tiêu đầu tiên là dán nhãn trạng thái Auto ISO rõ ràng, không tự quy đổi ISO hiệu dụng.

## Mới trong v0.6.9

1. `Movie → QVFIL Preview Guide` (read-only): báo đúng giá trị `RAW video > Preview` hiện hành.
   - `Auto`: cảnh báo có thể ưu tiên Framing chậm khi khung RAW nhỏ.
   - `Real-time`: báo Canon LiveView màu/nhanh nhưng có thể hiện ảnh nhỏ hoặc framing không trùng RAW.
   - `Framing`: báo slow/low-res nhưng đúng vùng RAW.
   - `Frozen LV`: báo không phù hợp lấy bố cục.
2. **Cinema slim**: Nếu camera đang Auto ISO (`!lens_info.raw_iso && lens_info.raw_iso_auto`), HUD ghi `ISO AUTO` thay vì số ISO giả định, chẳng hạn `ISO560`. Khi ISO là thủ công, hiển thị số như cũ. Dữ liệu RAW và độ nhạy thực tế không thay đổi.
3. Giữ nguyên toàn bộ Preview pipeline, `raw_rec_should_preview()`, `raw_rec_update_preview()`, `compress_task()`, `raw_video_rec_task()`. Các so sánh byte-identical được kiểm thử tự động.
4. Giữ 6 HUD modes, native Focus Peak, Shoot Check, Media Engine, Recording Report, Lossless Diag và LJ Error Guide.
5. **14-bit Lossless tiếp tục BLOCKED.** v0.6.9 KHÔNG sửa performance LiveView, không biến Canon Real-time thành Full-screen và không chạy hardware Lossless encoder.

## Quy trình nghiệm thu

**Không thay đổi thẻ v0.6.6 đã Hardware PASS.** Chỉ sau khi CI/ARM build PASS, có artifact và kiểm tra checksum trên thẻ TEST mới đưa v0.6.9 vào máy. Bản sao toàn bộ thẻ SD/CF đã được người vận hành báo cáo; chưa có kiểm tra restore độc lập.

### Đối chứng trước khi cài (không cần quay)

- Trên thẻ v0.6.6, ghi lại cấu hình `RAW video > Resolution, Data format, Preview` và ảnh LiveView ở Auto và Real-time trong STBY. Không thay đổi bit depth hoặc Lossless.
- Dùng đúng đối tượng sáng/độ phóng đại Lens, khung 1280×720/25fps 10-bit và trạng thái Display/Focus Peak tương đương để so sánh. Nếu v0.6.6 cho hành vi giống v0.6.8 thì đây là trade-off preview source, không phải regress riêng v0.6.8.

### Nếu cài 0.6.9 trên thẻ TEST

- Xác nhận `Movie → QVFIL Preview Guide`: thay đổi RAW Preview bằng tay từ `Auto` sang `Real-time`, sau đó quay về `Auto`; **chỉ quan sát STBY**. Guide phải đọc đúng lựa chọn và không tự thay đổi.
- Ở Auto ISO: `Cinema slim` cần hiển thị `ISO AUTO`. Ở manual ISO: `Cinema slim` hiển thị `ISO<giá trị>`. So với thanh gốc; không claim con số ISO auto.
- Giữ `QVFIL Lossless Diag` hiện `LJ OFF`; `QVFIL LJ Error Guide` hiện `HIST: ?`.
- Nếu Preview quá chậm hoặc bất thường, STOP thử nghiệm và quay lại thẻ v0.6.6 known-good; không thử lại Lossless hay 3K.
- Nếu đã chạy ổn trong STBY, có thể quay ngắn RAW 1280×720/25/10-bit không nén và kiểm tra `.MLV` trong MLV App. Không suy đoán chỉ từ màn hình.

## Trạng thái

- `V066_HARDWARE_PASS` (mốc khôi phục)
- `V068_DIAG_MENU_USER_PASS`
- `V068_REALTIME_COLOR_RETURNED_FRAME_SHRUNK`
- `V068_MLV_USER_PLAYBACK_PASS`
- `V069_PREVIEW_GUIDE_NOT_PREVIEW_FIX`
- `V069_AUTO_ISO_LABEL_CORRECTED_IN_SLIM`
- `V069_RAW_AND_PREVIEW_FUNCTIONS_BYTE_IDENTICAL_IN_TEST`
- `V069_HARDWARE_ACCEPTANCE_PENDING`
- `LOSSLESS14_BLOCKED`

**Hướng nghiên cứu sau:** Nếu thật sự cần full-frame LiveView màu/mượt với RAW 1280×720, phải đánh giá riêng khả năng và chi phí của việc nâng cấp raw_preview pipeline; không nên sửa bằng cách thay đổi crop/data trong RAW writer. Không cam kết full-screen real-time trên Digic 5 khi chưa benchmark thực tế.
