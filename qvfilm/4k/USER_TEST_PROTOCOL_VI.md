# QVFIL 4K Cinema — Hướng dẫn nghiệm thu tích hợp (Canon 5D Mark III)

**Trạng thái:** ENGINEERING PILOT, **chưa nghiệm thu trên máy ảnh**. Chỉ dùng với thẻ TEST có thể boot Magic Lantern, không dùng thẻ đang quay ổn định. Nguồn: bản build *đồng nhất* từ PR #46, **không phải** mô-đun thay thế đơn lẻ cho QVFIL 0.6.x / Magic Lantern 2025.

## Mục tiêu đúng
- Cấu hình "UHD 1:1" có chú thích trong source là **3840×1600 ~24p, crop 1:1** (2.40:1), **KHÔNG PHẢI** 3840×2160 UHD 16:9.
- Có đủ **màu + giám sát khung lớn + thao tác mượt STBY/REC** và MLV 4K-width thực sự. Khả năng 4K UHD 3840×2160 24/25p chưa được xác minh.
- Mỗi yêu cầu phải đạt độc lập. Việc MLV App phát video tốt **không chứng minh** LiveView mượt; giao diện hiện độ phân giải 4K **không chứng minh** file RAW đúng 4K.

## Bước 0 — An toàn bắt buộc (không phải một thử nghiệm mới)
1. Lưu bản sao toàn bộ thẻ Magic Lantern **đang hoạt động tốt** (đặc biệt \`autoexec.bin\`, \`ML/MODULES\`, \`ML/SETTINGS\`) ở máy tính; **không sửa thẻ đó**.
2. Chỉ dùng thẻ TEST riêng đã được chuẩn bị boot Magic Lantern đúng cách cho **Canon firmware 1.2.3**. Máy đã xuất hiện ID Probe \`FW:9.0.1 A6(34)\` nhưng đó là giá trị property đọc bởi ML, **không thay thế** kiểm tra firmware Canon ở menu Canon.
3. Chỉ sau khi kiểm tra file \`MANIFEST.json\` và SHA256, mới đưa các tệp nằm **bên trong** \`CARD_ROOT/\` của archive lên thư mục gốc thẻ TEST. Không thả nguyên archive vào thẻ. Không trộn thư mục/CFG của QVFIL v0.6.x vào thẻ.
4. **KHÔNG flash ML-SETUP.FIR, không thay boot flag/firmware, không dùng tính năng SD overclock, không bật card spanning khi khởi động pilot.** Bộ này không bao gồm bất kỳ \`.FIR\` nào. Không dùng thẻ TEST nếu không xác định chắc chắn nó đã có Magic Lantern bootable.
5. Pin đầy, máy đặt an toàn và thông thoáng. Ngừng ngay nếu freeze kéo dài, nóng bất thường, REC treo, file MLV lỗi, hoặc xuất hiện thông báo nguy hiểm. Tháo pin/chạy phục hồi chỉ theo quy trình Magic Lantern đã biết, không tháo thẻ khi đang ghi.

## Bước 1 — Một phiên thử tích hợp, không chụp từng menu

Trên thẻ TEST, lần đầu các mô-đun \`crop_rec.mo\` và \`mlv_lite.mo\` có thể cần được bật trong tab **Modules**, sau đó khởi động lại. **Mặc định từ bản pilot này là Crop OFF / RAW OFF / 10-bit uncompressed / More Hacks OFF.** Không cố bật 4K trước khi thấy máy hoạt động bình thường với hai mô-đun mới.

1. **Sanity (ngắn):** Movie / RAW video: bật ON, đặt 1920×1080 (hoặc chế độ nhỏ hơn theo hiển thị thật), 10-bit uncompressed, CF ưu tiên, card spanning OFF. Thử 10–15 giây, đảm bảo STOP sạch và xem được file MLV trong MLV App. Thao tác này chỉ xác nhận recorder trong bản mới.
2. **4K-width + Ultrafast, STBY:** Canon Movie 24p (23.976 nếu menu hiển thị vậy); Crop mode → \`UHD 1:1\`, **không** chọn \`4K 1:1 half-fps\`. Chú ý preset có thể cần thoát LiveView/Playback rồi vào lại để áp dụng. RAW video → Resolution: chỉnh phù hợp tối đa 3840×1600 có báo được, không nhập bừa thông số ngoài menu. Chọn Preview → **Framing**; Crop rec preview → **OFF** (tránh tự buộc chế độ gray). RAW video → Framed preview → Engine **ultrafast**; Comportment → Idle → **colored** / **half**; Timing **legacy**; Recording → **colored** / **quarter** (ưu tiên thời gian CPU; chỉ tăng lên half nếu không tụt frame). Chưa REC. Quay video điện thoại khoảng 10 giây khi lia máy chậm để xem hiển thị có đúng khung, màu, có trễ khó lấy nét không.
3. **4K-width REC:** Vì dữ liệu **3840×1600/24p 10bit không nén cần ~184 MB/s** trước overhead, không cố quay dài trong chế độ đó nếu thẻ không đủ băng thông đã đo. Để nghiệm thu khả năng **quay liên tục**, có thể lựa chọn \`12-bit lossless\` ở cùng crop nếu bản MLV Lite và dữ liệu thử thực tế xác nhận hoạt động; tỷ lệ nén và gánh nặng xử lý **không bảo đảm**. Thử một lần khoảng 15–30 giây để xác nhận ghi/STOP sạch, sau đó **tối đa 2–3 phút** khi tốc độ/buffer/temp ổn và không tụt frame. Ưu tiên dừng sớm hơn nếu dấu hiệu tràn buffer. Quay điện thoại 10 giây trong lúc REC để đo cảm nhận preview màu.
4. **Kiểm file trên Windows:** Copy nguyên \`.MLV\` và tất cả phần \`.M00\`, \`.M01\`, ... tương ứng; mở bằng MLV App. Xem metadata ghi được **RAWI width/height**, tần số frame và hiện tượng mất/corrupt frame. Chạy \`python qvfilm/4k/mlv_audit.py --json <các đường dẫn file MLV/M00...>\` nếu có Python 3; script này chỉ kiểm cấu trúc metadata, **không giải mã hình ảnh**.

## Mẫu báo cáo duy nhất (chỉ sau phiên thử)

| Chỉ tiêu | Kết quả |
|---|---|
| Canon Firmware thật | 1.2.3 / khác / chưa xác minh |
| MLV Lite & crop_rec cùng bản boot | Có / Không |
| RAWI resolution thật | W × H (từ MLV App) |
| Nominal FPS / Thực tế mất frame | ... |
| 4K crop \`UHD 1:1\` hoạt động | Có / Không |
| STBY Preview: có màu / đủ lớn / mượt | PASS / FAIL / N/A |
| REC Preview: có màu / đủ lớn / mượt | PASS / FAIL / N/A |
| Data format & clip duration | ... |
| Card speed đo trên máy (MB/s) | ... / chưa đo |
| Chạy 2–3 phút, không rớt frame / codec error | PASS / FAIL / chưa thử |
| MLV App phát tốt, hình sắc nét/crop đúng | PASS / FAIL |

**Không ghi \`QVFIL 4K Stable\` nếu chỉ một phần PASS.** Nếu crop 4K hoặc Preview fail, giữ card 1080p cũ; sửa theo lỗi nguyên nhân gốc từ báo cáo tổng hợp, không bắt anh thử hết từng submenu một lần nữa.

## Tại sao chưa gộp Cinema HUD QVFIL 0.6.x?

HUD của QVFIL v0.6.x được phát triển dựa trên Magic Lantern 2025. Bộ 4K này là Danne/Arnaud 5D3.123 nên khác API và ABI. Đưa HUD cũ vào trước khi xác nhận crop + recorder + preview sẽ làm tăng số biến gây lỗi; sau khi kiểm baseline 4K, chỉ port phần overlay/focus đã được đối chiếu API, không chuyển binary cũ sang.

**Không có đường tắt chắc chắn nào để tăng DIGIC5 từ vài Hz RAW-color rendering lên 25fps 4K realtime; ultrafast chỉ là một ứng viên cần đo trên máy.**
