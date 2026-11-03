# QVFIL v0.6.15 – ID Probe display-only formatter fix

## Nghiệm thu từ máy Canon 5D Mark III, ảnh IMG_5384, IMG_5385, IMG_5387 (03/11/2026)

Kết quả:
- **QVFIL v0.6.14** hiển thị đúng trong Movie/Cinema slim HUD.
- **QVFIL Color Lab OFF / SAFE OFF**: đúng quy trình an toàn.
- **QVFIL ID Probe** được nạp, nhưng màn hình hiển thị **M: 6s** và **FW: 10s** thay vì chuỗi model và firmware.
- Những chuỗi trên không phải giá trị thực tế của máy. Chúng tương ứng với phần độ dài của các format string cũ \`M:%.6s\` và \`FW:%.10s\`. Không được suy diễn Canon firmware sai hoặc model không được nhận diện từ ảnh này.

## Cơ chế lỗi

v0.6.14 gửi trường \`M:%.6s\` và \`FW:%.10s\` tới \`MENU_SET_VALUE\`/\`MENU_SET_RINFO\` (macro gọi formatter của Magic Lantern). Trên thiết bị, cách định dạng có precision này cho kết quả hiển thị sai. v0.6.15 không dùng precision ở format string nữa.

## Sửa chữa

Trong duy nhất module MLV Lite (sau khi chạy toàn bộ chuỗi patch tới v0.6.14):
- Đọc \`__camera_model_short\` vào \`char model_text[8] = {0}\` với tối đa 6 ký tự.
- Đọc \`firmware_version\` vào \`char fw_text[12] = {0}\` với tối đa 10 ký tự.
- Hiển thị \`MENU_SET_VALUE("M:%s", ...)\` và \`MENU_SET_RINFO("FW:%s", ...)\`.
- Nếu chuỗi đầu vào rỗng, hiển thị \`EMPTY\`.
- Không đọc serial hoặc ROM, không thay đổi property. Không mở khóa \`QVFIL Color Lab\`.
- Mỗi lần mở menu sẽ đọc lại các biến nội bộ; không lưu dữ liệu ra thẻ.
- Phiên bản trong Movie đổi thành \`QVFIL v0.6.15\`.

## Những gì KHÔNG đổi

- Macro nhận diện chính xác 5D3.123 và DIGIC 5, \`QVFIL_LAB_STBY\`, các giới hạn quay 10-bit/<=1600x900.
- \`raw_rec_update_preview()\`, \`raw_video_rec_task()\`, \`compress_task()\` byte-identical với v0.6.14; không mở rộng Canon YUV Real-time, không xử lý FPS.
- Giữ khóa lossless 14-bit; không chạm Canon firmware và autoexec.bin.
- Không thay đổi logic kích hoạt thử nghiệm: \`Color Lab\` OFF mỗi khi khởi động.

## Nghiệm thu trên thẻ TEST (chỉ sau khi CI PASS)

1. Giữ thẻ known-good nguyên vẹn. Chỉ thay **MLV_LITE.MO** trên thẻ TEST có bản sao lưu.
2. Khởi động, xác nhận Movie/Cinema slim HUD hiển thị \`QVFIL v0.6.15\`. Nếu sai dừng lại vì module cũ đang được nạp.
3. \`QVFIL Color Lab = OFF\`. Không quay RAW hay thử 14-bit.
4. Mở \`Movie → QVFIL ID Probe\`, chụp một ảnh đủ **M:** và **FW:**.
5. Kết quả có thể là:
   - \`M:5D3\` / \`FW:1.2.3\`: property đúng lúc kiểm tra; nếu Color Lab vẫn lỗi, cần phân tích timing, ABI, và logic kiểm tra khác.
   - \`M:5D3\` / \`FW:EMPTY\`: firmware property chưa được điền vào thời điểm đọc.
   - \`M:<khác>\` hoặc \`FW:<khác>\`: mô tả cụ thể mismatch, chưa thay firmware, vẫn khóa Lab.
6. Nếu vẫn hiển thị \`M:6s\`/\`FW:10s\`: đó là regression hoặc module cũ, chụp cả phiên bản và ngưng thử.
7. Nếu có lỗi máy, tắt nguồn và lắp thẻ known-good. Không flash.

**Trạng thái:** Source fix + CI, chưa nghiệm thu trên máy. Không cam kết khắc phục LiveView màu chậm.
