# QVFilm 5D Mark III — Quy trình chuẩn bị trước khi cài Magic Lantern

**Trạng thái: KHÔNG CÀI FIRMWARE Ở GIAI ĐOẠN NÀY.**

Đây là tài liệu hướng dẫn kiểm tra đầu vào dựa trên kết quả nghiệm thu thực tế của anh ngày 01/11/2026, không phải bộ cài và không thực hiện thay đổi bootflag.

## Những gì đã biết

- Thân máy: Canon EOS **5D Mark III** — ảnh gốc xác nhận.
- Mã hiển thị trong ảnh và ExifTool: **9.0.1 A6(34)** — mã MPU nội bộ.
- Theo ví dụ cộng đồng ExifTool, **MPU 9.0.1/A6 tương ứng ứng viên firmware Canon 1.2.3**. Tuy nhiên, firmware công khai của chính thân máy này **chưa được xác nhận độc lập**.
- \`qvfilm_compatibility_audit.json\`: \`NO_ML_FILES\`, \`ml_directory_present=false\`, \`module_names=[]\`, \`bootable_verified=false\`.
- \`NO_ML_FILES\` chỉ áp dụng cho **đường dẫn thẻ đã quét**. Không tự động kết luận chưa từng cài Magic Lantern trên máy.
- Trạng thái cài đặt hiện tại: \`HOLD_NOT_APPROVED\`.

## Công việc anh có thể thực hiện an toàn

1. **Xác định đúng thẻ:** Gắn thẻ CF/SD vừa lấy từ chiếc Canon 5D Mark III vào Windows. Mở File Explorer và đối chiếu ổ đĩa vật lý, dung lượng và các file ảnh mới anh biết chắc được chụp bằng máy này. Nếu đúng thẻ Canon thường, không thấy thư mục \`ML\` là bình thường. Không định dạng, không chép file hack.
2. **Kiểm tra Magic Lantern đã cài hay chưa:** Dùng **thẻ đang dùng hằng ngày trên máy**. Khi máy ở trạng thái không ghi dữ liệu, kiểm tra xem nhấn nút thùng rác/ERASE có mở giao diện Magic Lantern hay không (trong chế độ quay/chụp phù hợp). Nếu không mở được, ghi lại hiện tượng; không thử các bản \`.FIR\` lạ.
3. **Xác minh firmware Canon:** Đối chiếu với một nguồn độc lập tin cậy, chẳng hạn thông tin hỗ trợ của Canon hoặc kỹ thuật viên hiểu 5D Mark III. EOS Utility có thể giúp xem thông tin máy qua USB nhưng **không bảo đảm** cho ra phiên bản firmware công khai khác với dữ liệu đã có.
4. **Sao lưu:** Chép ảnh/video từ thẻ về PC. Nếu có **thẻ Magic Lantern đã từng khởi động thành công**, giữ nguyên thẻ, dùng QVFilm Backup/Verify SHA-256 để sao lưu file. Chưa có thẻ ML tốt thì **không đánh dấu "có phương án khôi phục"**.
5. **Chuẩn bị thẻ thử riêng:** Sau khi các mục trên rõ ràng, chọn một thẻ SD/CF khác, chưa có dữ liệu quan trọng. Không thực hiện bước cài ML trên thẻ này khi chưa có gói cài baseline đã được kiểm tra tương thích.

## Thứ tự sau khi điều kiện được xác nhận

- **Bước A:** Cài và nghiệm thu một bản **Magic Lantern nền chuẩn cho 5D3.123** có hướng dẫn, nguồn và checksum đáng tin; không trộn các module từ các nhánh khác nhau.
- **Bước B:** Nghiệm thu khởi động, MENU, LiveView, chụp Canon bình thường, chức năng quay gốc và thử quay RAW mức thấp; chuẩn bị phương án dừng thử an toàn.
- **Bước C:** Mới kiểm tra QVFIL Dashboard v0.1.0 đã biên dịch được, nhưng chưa xác thực trên LCD thực tế.
- **Bước D:** Chỉ sau khi các bước trên ổn định mới nghiên cứu preset Cinema RAW 3K và hiệu năng thẻ/khung hình rơi.

Không dùng \`5D3.123\` để cài trên thân máy có firmware khác; không nâng/hạ firmware Canon tùy tiện. Kết quả compiler PASS **không đồng nghĩa** máy khởi động an toàn.

**Mã nguồn và checklist kỹ thuật:** \`docs/QVFILM_5D3_FIRST_INSTALL_READINESS.md\`. Bộ kiểm tra tự động: \`qvfilm/preflight/install_readiness.py\` (chỉ đọc audit JSON, không can thiệp máy).

Các nguồn:
- https://github.com/exiftool/exiftool/issues/399
- https://builds.magiclantern.fm/
- https://www.usa.canon.com/support/p/eos-5d-mark-iii
