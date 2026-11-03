# QVFIL v0.6.20 — So sánh Full / 2 dải / 3 dải trên Canon 5D Mark III

## Nghiệm thu v0.6.19 (5 ảnh IMG_5399–5403)
- Máy nhận đúng `QVFIL v0.6.19`, `ROM:672EEACE SIG PASS`, RAW 1280×720, 10-bit, LJ OFF.
- Chế độ đầy đủ `Color STBY` đạt `C:138`, `F:138 215ms`, `AVG:208ms`, `Hz:3.4`. Đây là phép đếm xử lý màu chứ KHÔNG phải LCD FPS.
- Đã chọn `Stripe STBY` nhưng ảnh menu vẫn ở `ARMED 0F`, `WAIT LV B:0/3`. Ảnh LiveView cuối chỉ cho thấy hình; không có ảnh menu sau khi chạy để biết bộ đếm dải/sweep.
- **Chưa thể kết luận Stripe 3 nhanh hơn chế độ Full.** Bằng chứng v0.6.19 hiện chưa đủ để đánh giá hiệu năng Stripe.
- Việc hiển thị màu chưa chứng minh ảnh chuyển động mượt. Chấm sáng có thể là Focus Peaking; không thể xác nhận chỉ từ ảnh.

## Thay đổi mã nguồn trong v0.6.20
- Tùy chọn `Movie → QVFIL Color Lab`: `OFF` (mặc định sau bật máy), `Color STBY` (toàn khung đối chứng), `Stripe 2` và `Stripe 3`.
- Tiếp tục gọi cùng bộ xử lý màu cũ `raw_preview_fast_ex`, chỉ thay hai tham số `LV y1/y2` theo 2 hoặc 3 dải trong STBY.
- `Color Perf` hiển thị thời gian/nhịp hoàn tất **mỗi lượt**. Ở Stripe, mỗi lượt chỉ là 1 dải; KHÔNG được gọi đây là FPS toàn khung.
- `Color Sweep` hiển thị số lượt hoàn thành đủ dải `C:<số>`, thời gian giữa hai lượt quét `T:<ms>`.
- Mục **mới** `Color Sweep Rate` trong menu tên `QVFIL Sweep Rate` hiển thị `AVG:<ms>` và `Hz:<x.y>` cho lượt quét đủ chiều cao, tách với `Color Perf`. Đây vẫn KHÔNG phải khung đồng bộ hay LCD FPS; các dải có thể có độ trễ hình khác nhau.
- Khi chọn chế độ mới và quay lại LiveView, đặt lại F / AVG / khoảng giữa lượt / tổng sweep nhằm tránh dùng số liệu của chế độ cũ.
- Không thay `raw_video_rec_task`, `compress_task`, file MLV, bộ giải màu lõi, vùng nhớ ROM, autoexec.bin, Canon firmware, thẻ ghi, DMA. Chỉ hoạt động khi mọi điều kiện 5D3, DIGIC5, `ROM Check SIG PASS`, Movie LiveView 1×, RAW IDLE, RAW ON, 10-bit không nén, nguồn sensor 14-bit, độ phân giải ≤1600×900 đều hợp lệ.
- **Không hứa tăng tốc hoàn thành cả khung.** Tách 2/3 dải có thể giảm blocking mỗi lượt nhưng nhiều lượt dựng gamma bảng lại làm tổng thời gian tăng.

## Quy trình nghiệm thu v0.6.20 (thẻ TEST)
1. Giữ thẻ SD/CF đã quay ổn định nguyên vẹn. Dùng bản sao thẻ TEST và chỉ thay `ML/MODULES/MLV_LITE.MO`. Không flash firmware, không thay `autoexec.bin`.
2. Bật máy: `Movie → Cinema slim HUD` phải hiện `QVFIL v0.6.20`; `Color Lab` mặc định OFF.
3. Đặt RAW 1280×720, 10-bit Uncompressed, 25fps, Movie LV 1x. Vào `QVFIL ROM Check`, yêu cầu `ROM:672EEACE SIG PASS`; nếu không PASS, dừng.
4. Cố định cùng một cảnh có cả vật màu đỏ/xanh/trắng với tripod. Chọn `Color STBY`, thoát menu và quan sát 15–20 giây. Mở lại menu và chụp 3 dòng `QVFIL Color Perf`, `QVFIL Color Sweep`, `QVFIL Sweep Rate`. Chụp một ảnh LiveView không mở menu.
5. Đổi `OFF`, rồi sang `Stripe 2`. Lặp lại bước 4 ở cùng cảnh. Để ít nhất 2 lượt quét hoàn thành (có `C:2` trở lên) trước khi đọc `Sweep Rate`.
6. Đổi `OFF`, rồi sang `Stripe 3`. Lặp lại, đọc `C`, `T` và `Sweep Rate`.
7. Đánh giá hiện tượng giật, xé ngang, đảo màu, độ trễ khi lia máy. Nếu có bất thường, chuyển Lab OFF và khởi động lại. Trong vòng thử này **chưa bấm REC**.
8. Gửi ảnh tương ứng mỗi chế độ, đặc biệt **ảnh sau khi Stripe 2/3 đã hoàn tất vài lượt quét**, không chỉ ảnh `ARMED 0F`. Có thể gửi đoạn video điện thoại quay LCD khi lia nhẹ để so sánh chủ quan.

**Trạng thái:** mã nguồn và kiểm thử CI cần PASS; chưa được nghiệm thu trên máy. V0.6.20 là thử nghiệm A/B, chưa phải bản hoàn thiện LiveView 25fps.
