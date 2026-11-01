# QVFilm — Magic Lantern 5D3 v0.4.0: Nghiệm thu quay MLV RAW lần đầu

## Trạng thái

Canon 5D Mark III + Magic Lantern \`2025-06-20.5D3.123\`: cài và khởi động PASS; 6/6 bài kiểm tra Canon gốc PASS; ROM0/ROM1 đã được người dùng sao lưu. RAW chưa nghiệm thu.

**Giữ nguyên thẻ SD Magic Lantern đang hoạt động. Không cài module QVFIL tùy biến lên đó.**

## A. Xác nhận module RAW của bản nền

1. Pin đầy, máy ở Movie/LiveView, nhấn nút **ERASE** để mở Magic Lantern.
2. Chuyển đến tab **Modules** (biểu tượng nhiều ô vuông).
3. Chụp ảnh rõ toàn bộ danh sách. Nếu có \`mlv_rec\`, chỉ bật \`mlv_rec\` (không bật đồng thời nhiều module ghi RAW như \`raw_rec\` / \`mlv_lite\`).
4. Nếu chỉ thấy các tên module khác, chưa tự bật — gửi ảnh để xác định trước.
5. Sau khi bật đúng \`mlv_rec\`, thoát menu và khởi động lại máy bình thường.
6. Mở Magic Lantern → tab **Movie**; xác nhận mục **RAW video (MLV)** xuất hiện. Chụp ảnh trang Movie và submenu RAW (thường dùng **Q** để mở submenu).

## B. Thử một clip ngắn

Khi có mục MLV RAW và các giá trị phù hợp:

- 1280×720, 23.976/24p, quay 5–10 giây, chưa cần audio.
- Các chế độ crop, HDR, pre-record, high FPS, 3K/4K: **OFF**.
- Nếu báo thiếu tốc độ ghi trên SD, giảm xuống một độ phân giải nhỏ hơn do module cung cấp (ví dụ 960×540), hoặc tạm dừng. Không cố bắt máy ghi liên tục.
- Giữ nguyên các tùy chọn nhạy cảm không hiểu rõ. Nếu module cho phép chỉnh bit depth, trước tiên sử dụng một lựa chọn hỗ trợ chắc chắn, không ép các chế độ thử nghiệm.
- Sau khi quay, dừng bình thường, sao chép file \`.MLV\` sang PC. Không xóa file gốc trên thẻ.

## C. Kiểm tra trên Windows 10

Công cụ kỹ thuật v0.4.0 \`qvfilm/preflight/inspect_mlv.py\` chỉ kiểm tra:

- File \`.MLV\` tồn tại, dung lượng hợp lý, 4 byte đầu là \`MLVI\`.
- SHA-256 phục vụ đối chiếu bản sao.
- Không ghi lên máy ảnh/thẻ, không đọc ROM.

Ví dụ:

\`\`\`powershell
py -3 inspect_mlv.py --mlv "Z:\5D Mark III Upgrade\RAW_TEST\M26-0001.MLV"
\`\`\`

Báo cáo được tạo trong thư mục \`reports/qvfilm_mlv_first_take.json\` bên cạnh script. **PASS của script chưa chứng minh khung hình không rơi, video giải mã được, hay màu sắc đúng.**

Dùng MLV App (https://mlv.app/) mở clip và quan sát video; kiểm tra khung hình lỗi, thời lượng, thông số ghi, rồi thử xuất CinemaDNG hoặc một đoạn video mẫu.

## D. Chuyển sang Full HD và 3K khi nào?

- Full HD RAW 1920×1080 ở 24p 14-bit chưa nén xấp xỉ 87 MB/s **trước overhead**; thẻ SD của 5D III thường không đủ tốc độ ghi lâu dài.
- Để nghiệm thu Full HD, ưu tiên CF UDMA 7 tốc độ ghi bền vững cao; cần kiểm tra **thẻ ghi thực tế**, không dựa vào tốc độ quảng cáo.
- Sau Full HD ổn định, mới đánh giá nhánh crop_rec/3K. Bản QVFIL thử nghiệm hiện được build từ **fork khác** và **chưa chứng minh tương thích ABI** với bản ML 2025; tuyệt đối chưa thay module RAW đã hoạt động bằng file \`.mo\` tùy biến.

## E. Thông tin gửi lại để tiếp tục

- Ảnh tab **Modules** cho thấy tên và trạng thái bật/tắt module.
- Ảnh tab **Movie → RAW video** và submenu độ phân giải.
- Model/loại thẻ SD và CF anh có.
- Nếu đã quay thử: thời lượng clip, có cảnh báo buffer/dropped frames không, MLV App có mở được không; gửi JSON từ \`inspect_mlv.py\` nếu cần.

Nếu có lỗi hoặc máy nóng/treo, dừng thử, không chép module khác hoặc chạy lại Firmware Update. Giữ nguyên thẻ nền và file ghi lỗi để chẩn đoán.

Mã nguồn/checklist tiếng Anh: \`docs/QVFILM_5D3_MLV_BASELINE_ACCEPTANCE_v0.4.0.md\`.
