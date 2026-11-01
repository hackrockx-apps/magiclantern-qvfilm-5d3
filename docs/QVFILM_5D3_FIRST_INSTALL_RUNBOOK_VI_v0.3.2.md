# QVFilm 5D3 — Hướng dẫn cài Magic Lantern NỀN lần đầu (v0.3.2)

**Chỉ dành cho Canon EOS 5D Mark III với Canon public firmware 1.2.3.**
**Bản Magic Lantern nền:** \`magiclantern.2025-06-20.5D3.123.zip\`.
**Không phải bản QVFIL tùy biến.**

## Tình trạng đã xác nhận

- Thân máy 5D Mark III; mã nội bộ MPU \`9.0.1 A6(34)\`.
- Anh xác nhận **PASS bước đọc firmware Canon 1.2.3**. Đây là xác nhận từ người vận hành; repository **không lưu bằng chứng kỹ thuật độc lập (ví dụ ảnh EOS Utility)**.
- Cả SD và CF đang dùng đều không có các file \`ML/\` hay \`autoexec.bin\`. Điều đó **không chứng minh bootflag NVRAM chưa được thiết lập**.
- Bộ ZIP 2025 \`5D3.123\` có 53 file, \`ML-SETUP.FIR\`, \`autoexec.bin\`, \`ML/\`, và hash SHA-256:
  \`63ca9e56405573ce58f9fca2680d17bb87ce57a5b946f66afc2cbb16ccf00d77\`
  bằng giá trị trên ảnh trang tải Magic Lantern do anh cung cấp.
- QVFIL \`mlv_lite.mo\` tùy biến **chưa được kiểm tra trên máy thật**. Không trộn vào bản nền lần đầu.

## Điều kiện bắt buộc trước khi nhấn Firmware Update

1. **Máy ảnh đang hoạt động bình thường** ở firmware gốc Canon: chụp ảnh, menu, quay H.264.
2. Firmware trên máy đúng **Canon 1.2.3** theo kết quả xác nhận của người sử dụng. Nếu có một dấu hiệu mâu thuẫn (ví dụ EOS Utility / máy báo một phiên bản khác), dừng.
3. Pin LP-E6 đầy và khỏe; không dùng nguồn không ổn định. Tránh tất cả cáp và thiết bị ngoại vi.
4. Có **thẻ SD dự phòng chuyên dụng** (ưu tiên 8–32GB) không chứa dữ liệu quan trọng. **Không sử dụng lại thẻ SD/CF đang chứa ảnh**, không định dạng nhầm.
5. Sao lưu riêng các file Canon (ảnh/clip) từ thẻ dùng hằng ngày ra PC.
6. Đã hiểu \`Firmware Update\` ở bước này chạy **trình cài Magic Lantern** \`ML-SETUP.FIR\`, không phải firmware Canon; chương trình cài có thể đặt bootflag bền vững trong bộ nhớ máy. Không thể hứa rằng tháo thẻ chữa được mọi trường hợp lỗi.

## Chuẩn bị thẻ SD riêng (chỉ làm với thẻ thử!)

1. Tắt máy, lấy thẻ CF ra, chỉ cắm thẻ **SD thử** vào máy. Kiểm tra chắc chắn không phải thẻ đang chứa ảnh công việc.
2. Trên máy Canon: \`MENU → Format card\`, chọn đúng thẻ SD thử; format. **Format xóa dữ liệu trên thẻ**.
3. Tắt máy, lấy thẻ SD thử ra, gắn vào đầu đọc trên Windows 10.
4. Mở \`magiclantern.2025-06-20.5D3.123.zip\` đã có hash xác thực. Giải nén **nội dung của ZIP trực tiếp vào gốc thẻ SD thử**; không giải nén vào một thư mục con, không thay bằng bất kỳ file QVFIL nào.
5. Tại gốc thẻ phải nhìn thấy:
   - \`X:\autoexec.bin\`
   - \`X:\ML-SETUP.FIR\`
   - \`X:\ML\` (thư mục chứa các file/module của bộ nền)
6. Kiểm tra lại \`X:\` **đúng là thẻ SD thử**; an toàn tháo thẻ (Eject), rồi lắp lại vào Canon. **Chưa nhấn Firmware Update nếu bất kỳ điều kiện nào chưa đạt**.

## Cài bản Magic Lantern NỀN trên máy

> Phần này thực hiện bằng tay với người vận hành hiện diện. Không có script QVFilm nào ra lệnh cài lên máy.

1. Xác nhận đúng thẻ SD thử, không có CF. Lắp pin đã sạc đầy; ngắt cáp USB/HDMI.
2. Bật 5D Mark III; xoay vòng chế độ sang \`M\`. Máy phải hoạt động bình thường trước khi bắt đầu.
3. \`MENU → Setup (cờ lê vàng) → Firmware Ver. → SET\`.
4. Chỉ tiến hành nếu trình cài nhận đúng **Magic Lantern cho Canon 5D Mark III 1.2.3**. Nếu thấy bản khác, lỗi, cảnh báo không hiểu hoặc trình cài Canon firmware từ nguồn khác: **Cancel và dừng**.
5. Xác nhận chạy \`ML-SETUP.FIR\`, **không thao tác khi đang chạy**. Không tắt nguồn hay rút thẻ khi còn hoạt động. Đọc và làm theo **chính xác thông báo trên LCD**. Một số bản yêu cầu khởi động lại khi kết thúc; không suy đoán thời gian đếm ngược.
6. Khi LCD thông báo hoàn thành và yêu cầu restart, tắt máy theo chỉ dẫn, đợi máy tắt hoàn toàn rồi bật lại với thẻ SD thử.

## Nghiệm thu sau cài

- Máy khởi động, menu Canon và chụp ảnh thông thường hoạt động.
- Ở chế độ phù hợp, nhấn **ERASE/thùng rác** để mở menu Magic Lantern. Chỉ cần xác nhận menu xuất hiện.
- Không bật ngay module RAW/crop_rec/3K; chưa chép module QVFIL tùy biến.
- Kiểm tra mở LiveView, chụp ảnh Canon, quay H.264 ngắn, tắt/mở nguồn một lần.
- Chụp ảnh LCD khi cài thành công và menu ML, tránh lộ serial. Lưu thêm log/thông báo lỗi nếu có.

## Điều kiện dừng và khôi phục

- Nếu thấy pin yếu, file không nhận, sai phiên bản, LCD báo ERROR hoặc đèn ghi thẻ kéo dài bất thường: **dừng, không lặp lại thao tác**. Nếu đang chạy installer, làm theo hướng dẫn tại chỗ thay vì ngắt nguồn đột ngột.
- Nếu treo sau khi đã restart: tắt máy nếu có thể, đợi đèn ghi thẻ ngừng sáng, tháo thẻ thử khi máy đã tắt; có thể tháo/lắp lại pin nếu cần. Nếu bật không thẻ vẫn thất bại, dừng và tìm người sửa Canon/Magic Lantern có kinh nghiệm.
- **Đừng nhầm "bật máy không dùng ML" với gỡ cài đặt**: bootflag có thể còn. Để gỡ ML thực sự cần thủ tục uninstall phù hợp với build và thân máy, không chỉ xóa file.
- Không dùng sản phẩm thực tế/không thể quay lại cho đến khi bản nền vượt kiểm tra vận hành.

## Checkpoint QVFilm

- Nếu nền Magic Lantern cài thành công, chụp ảnh menu và báo kết quả. Sau đó chúng ta sẽ đánh giá boot/menu/LiveView trên thẻ thử **trước** khi bật QVFIL.
- Nếu lỗi, giữ nguyên thẻ và log, ghi lại nguyên văn thông báo; không tự flash/hạ firmware Canon.
- \`master\` và nhánh \`qvfilm/v0.1.0-ui-prototype\` vẫn chưa merge, không ảnh hưởng các bản nền.

## Nguồn tài liệu

- https://magiclantern.fandom.com/wiki/Unified/Install
- https://builds.magiclantern.fm/
- https://magiclantern.fandom.com/wiki/Unified/UserGuide
- https://github.com/exiftool/exiftool/issues/399
