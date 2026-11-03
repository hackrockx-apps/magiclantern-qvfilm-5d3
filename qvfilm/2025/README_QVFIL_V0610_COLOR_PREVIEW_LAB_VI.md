# QVFIL v0.6.10 – Color Preview Lab (Canon 5D Mark III / 5D3.123)

## Phân tích giới hạn DIGIC 5

Đã đọc chính xác Magic Lantern source 2025 commit `ed3e7c0dfacfdeaf3349dee73edf9e3621217462`:

- `RAW video → Preview Auto` tự chọn `Framing` với RAW có `res_x < 80%` độ phân giải sensor tối đa; ở 1280×720 khả năng cao rơi vào nhánh này.
- `Preview Real-time` dùng Canon LiveView màu/mượt nhưng không đảm bảo đúng crop RAW, đôi khi khung nhỏ có viền đen.
- `raw_preview_fast_ex` hỗ trợ đúng **hai kiểu hiển thị**: `RAW_PREVIEW_COLOR_HALFRES` (360×480, nặng CPU) hoặc `RAW_PREVIEW_GRAY_ULTRA_FAST` (180×240, hướng tới mượt hơn). Không có sẵn engine color full-res high-FPS để bật bằng một cờ cấu hình.
- `raw_rec_update_preview` dùng `raw_set_preview_rect(..., obey_info_bars=1)`: dành 38 px trên và dưới cho info bar; khi STBY ngủ 50 ms giữa các lần vẽ màu. Trong quá trình REC, nếu hàng đợi ghi đầy, nó sẽ dùng gray-ultra-fast và nghỉ 500/1000 ms để ưu tiên an toàn dữ liệu.
- Người vận hành v0.6.9: `Real-time` màu/mượt nhưng hình nhỏ; `Auto` gần trắng đen, load chậm. Người dùng đã xác nhận trước đó file MLV 1280×720/10bit mở trong MLV App có hình ảnh tốt. Không có chứng cứ giảm chất lượng RAW do preview.

**Không thể hứa cùng lúc màu đẹp, full frame và 25fps trên DIGIC 5 bằng bản vá nhẹ.** Bản 0.6.10 là thí nghiệm một cách có kiểm soát để cải thiện *diện tích* và *chu kỳ cập nhật STBY* bằng các hàm đã có của Magic Lantern, không xây dựng mới bộ khử Bayer.

## QVFIL Color Preview Lab (mới)

`Movie → QVFIL Color Preview Lab → OFF / Color large STBY`.

- **OFF khi mỗi lần khởi động**, không có `MODULE_CONFIG` cho lựa chọn này. Người dùng phải tự bật trong từng phiên.
- Chỉ thử trên 5D3.123, Movie LiveView x1, RAW 10-bit uncompressed, <=1600×900, `RAW video > Preview: Auto hoặc Real-time`, và chỉ khi RAW recorder đang **RAW_IDLE**.
- Khi bật ở STBY: bắt buộc chọn RAW Framing màu qua **display filter cũ**, không xây dựng callback khác; gọi `raw_set_preview_rect(...,0)` để sử dụng cả vùng trước đây dành cho info bars. `raw_force_aspect_ratio` vẫn giữ nguyên.
- Dùng chính `RAW_PREVIEW_COLOR_HALFRES` của Magic Lantern. Theo thời gian `DRAW Xms` đo được từ một lượt render, khoảng nghỉ giữa các lượt đổi thành 20 ms nếu render dưới 40 ms, 35 ms nếu dưới 80 ms, hoặc giữ 50 ms nếu chậm hơn. **Không phải tốc độ khung hình thực; không có số fps bảo đảm.**
- Khi bắt đầu REC, ở x10 LV, khi AF hoặc ở chế độ RAW/preview khác, Lab tự không can thiệp: quay lại đường hiện hữu của Magic Lantern với mọi cơ chế tiết lưu hàng đợi 500/1000 ms.
- Không thay đổi `raw_video_rec_task`, `compress_task`, các slot, write queue, lens ISO, CF, RAW codec, hay các firmware/boot flags.
- Lossless 14-bit vẫn bị BLOCKED.
- Mọi HUD đã nghiệm thu, Focus Peak và Preview Guide giữ nguyên.

## Tiêu chí nghiệm thu an toàn

**Chỉ sau khi exact-source unit tests và ARM build PASS.** Bản v0.6.6 của người dùng vẫn là thẻ known-good. V0.6.10 phải được kiểm tra trên thẻ boot TEST đã sao lưu, kiểm tra checksum `MLV_LITE.MO`. Không dùng bản này làm máy quay sản xuất trước nghiệm thu.

1. Xác nhận `Movie → QVFIL Cinema HUD` hiện `v0.6.10`, `Color Preview Lab` mặc định **OFF**, và `LJ OFF`.
2. Đặt `RAW video 1280×720 / 10-bit / 25p / Preview Real-time` rồi chụp một ảnh STBY trước khi bật Lab. Không bấm REC.
3. Bật `QVFIL Color Preview Lab → Color large STBY`. Thoát menu, so ảnh **cùng bố cục**: chiều rộng, chiều cao khung, chất lượng màu, độ trễ khi lia/lấy nét tay. Đây là chế độ dùng RAW Framing và có thể **chậm hơn** Canon Real-time, dù diện tích lớn hơn.
4. Kiểm tra với `Preview Auto` ở STBY để đối chiếu; không cho rằng Auto mặc định là preview màu tốt. Chụp cả kết quả `DRAW Xms` nếu có.
5. Nếu màu bất thường, preview giật/treo hoặc máy nóng nhanh: tắt Lab về **OFF** hoặc khởi động lại để tự OFF. Không tiếp tục quay thử.
6. Nếu STBY đạt mức sử dụng được, thử quay một file RAW 5–10 giây **trên thẻ TEST**, không nén, tối đa cấu hình đã nghiệm thu; khi REC Lab phải tự nhường lại RAW Preview mặc định, không tiếp tục ép render. Mở .MLV trong MLV App và kiểm tra màu, chuyển động.
7. Nếu có bất kỳ lỗi nào thì tắt máy và quay lại thẻ v0.6.6 đã PASS. Chưa thử 14-bit Lossless/3K/overclock.

**Các câu hỏi nghiệm thu:** Màu có tốt hơn không? Preview lớn thêm bao nhiêu? Độ mượt thực tế STBY có đạt không? Có khác gì khi REC? Không đặt mục tiêu FPS khi chưa đo được.

## Kết quả đạt và chưa đạt

- Source regression có kiểm tra recorder và compressor **byte-identical** so với v0.6.9.
- Code opt-in, không lưu qua lần boot, có guard 5D3.123 / STBY / x1 / 10bit / <=1600×900 / Auto-or-Real-time.
- `RAW_PREVIEW_COLOR_HALFRES` là engine cũ; hình vẫn có thể chậm, sai màu do white-balance xấp xỉ. Chưa có phương án safe để đạt chuẩn màu kiểu Blackmagic/Pocket trên LCD 5D3.
- Module chưa được nghiệm thu trên thân máy; build PASS (nếu có) chỉ chứng minh biên dịch, không chứng minh an toàn khi chạy.
