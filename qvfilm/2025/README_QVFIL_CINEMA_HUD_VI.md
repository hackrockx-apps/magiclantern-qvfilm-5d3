# QVFIL Cinema HUD v0.5.0 — Canon EOS 5D Mark III (5D3.123)

## Đã triển khai trong mã nguồn

Phiên bản này được thiết kế **trên đúng Magic Lantern Development 2025-06-20, commit ed3e7c0df**, không ghép module đã biên dịch từ các nhánh cũ của fork.

### 1. Khoanh vùng lỗi 14-bit lossless

Ảnh và log từ camera cho thấy module gốc bị \`ASSERT(0)\` tại \`mlv_lite.c:2742\` trong tác vụ \`compress_task\`. Bảy log đều thiếu mã lỗi trả về của \`lossless_compress_raw_rectangle()\`, nên chưa xác định gốc lỗi là \`-1\`, \`-2\` hay \`-3\`.

**Giải pháp ở v0.5.0 là an toàn trước, không phải sửa được bộ nén:**

- Tại đầu \`raw_video_rec_task()\`, chỉ trên thân máy \`5D3.123\`, nếu chọn bất kỳ định dạng **lossless compression**, thông báo \`QVFIL: Lossless blocked. Use RAW uncompressed.\` rồi **không bắt đầu ghi**.
- Không thay đổi đường ghi RAW không nén đã chạy PASS 1280×720 25p, 10-bit.
- **14-bit uncompressed** vẫn là lựa chọn 14-bit thực sự, nhưng băng thông cao và cần CF đủ tốc độ. Đây là **định dạng khác** với 14-bit lossless, không được ghi nhãn sai là lossless.
- Giữ nguyên mã ASSERT ở đường nén để không âm thầm ghi buffer hỏng, không cố đổi một mã lỗi nén thành frame hợp lệ.
- Không tự downgrade Canon firmware, không cập nhật bootflag, không ghi lên máy hoặc thẻ.

Mục tiêu giai đoạn sau: ghi nhận mã lỗi âm và nghiên cứu cơ chế encoder hardware khởi tạo/timer/JPEG trên **bản 2025 chính xác**, với quy trình mô phỏng và thử trên thẻ riêng. Chưa có bằng chứng đủ để công bố lossless đã sửa xong.

### 2. QVFIL Cinema HUD — giao diện lấy cảm hứng từ máy quay cinema

Giao diện đơn giản, đọc được trên LCD 5D Mark III:

- Dải LiveView phía trên: \`QVFIL  STBY/REC  25.00\`, REC có chữ đỏ.
- Dải phía dưới: \`1920x1080  10b RAW  ISO2000\` (giá trị thật từ recorder/camera).
- Bật/tắt qua **Movie → QVFIL Cinema HUD** (mặc định OFF). Không xóa menu Movie; không chuyển nút Record; không thay đổi phần firmware Canon.
- Giao diện dùng chính API **LVInfo** của Magic Lantern và chạy trong luồng vẽ thanh thông tin, không vẽ đồ họa nặng mỗi VSYNC; không tự can thiệp vào vùng hình/RAW buffer.
- Đây là **HUD v0.5.0** lấy cảm hứng từ cách phân cấp thông tin trên camera cinema, **không phải sao chép giao diện/logo của Blackmagic**. Các mục như waveforms, false color, histogram, timecode và bố cục màn hình đầy đủ sẽ cân nhắc sau khi HUD ban đầu nghiệm thu ổn định.

Để thấy HUD, máy cần Movie LiveView và Magic Lantern Global Draw bật, đồng thời mục Cinema HUD ON.

### 3. Mã nguồn, cách biên dịch

- \`qvfilm/2025/apply_qvfilm_patch.py\`: chỉnh duy nhất \`modules/raw_video/mlv_lite/mlv_lite.c\`, áp dụng **chỉ** cho Git checkout commit \`ed3e7c0dfacfdeaf3349dee73edf9e3621217462\`.
- \`qvfilm/2025/test_patch_2025.py\`: các bài test kiểm tra giữ nguyên Movie, có HUD, guard không cho lossless khởi chạy và từ chối áp dụng hai lần.
- \`.github/workflows/qvfilm-2025-cinema-hud.yml\`: GitHub Actions tải đúng source 2025, biên dịch core 5D3.123 và module trên Linux cross compiler ARM, lưu **chỉ logs và diff nguồn**.
- **KHÔNG phát hành file .MO/.FIR để cài trên máy** khi chưa qua build/test/đánh giá ABI và phương án rollback. PASS biên dịch không đồng nghĩa PASS quay 14-bit.

### 4. Tiêu chí nghiệm thu phần cứng sau này (chưa thực hiện)

1. Giữ thẻ Magic Lantern 2025 gốc và ROM backup tại PC, không ghi đè.
2. Trên thẻ thử thứ hai, nghiệm thu riêng firmware/module tương thích hoàn toàn với bản chạy tốt. **Không ghép module từ fork 2018**.
3. Kiểm tra Canon menu, Movie, LiveView, HUD bật/tắt, hiển thị đúng FPS/ISO/RAW, điều khiển không lag; quay 10-bit uncompressed và MOV decode/export như baseline.
4. Khi chọn 14-bit lossless, **phải từ chối ghi với thông báo dễ hiểu**, không rơi vào màn hình ASSERT; không phát sinh file RAW hỏng.
5. Chỉ sau đó mới nghiên cứu lossless thực sự và khả năng 3K Cinema RAW; yêu cầu kiểm tra tốc độ CF và dropped frames.

**Trạng thái:** SOURCE-CUSTOMIZATION IN PROGRESS / BUILD CHECK / NOT INSTALLABLE.
