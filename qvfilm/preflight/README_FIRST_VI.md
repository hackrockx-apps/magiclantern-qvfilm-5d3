# QVFilm 5D3.123 — Gói kiểm tra tương thích & dự phòng an toàn v0.2.2

**Dành cho Windows 10. Chỉ kiểm tra và sao lưu. KHÔNG chứa firmware để cài vào máy.**

Máy mục tiêu: **Canon EOS 5D Mark III**, firmware công khai **1.2.3**, nền Magic Lantern `5D3.123`.

## BẢN V0.2.1 — SỬA LỖI WINDOWS 10

Bản này khắc phục hai sự cố đã thấy trong ảnh nghiệm thu: `ExifTool not found` và `unrecognized arguments: Mark III Upgrade...`.

**Đường dẫn thư mục có dấu cách:** `QVFILM_START_WIN10.cmd` giờ chỉ khởi chạy `preflight.py interactive`. Python trực tiếp đọc đường dẫn anh nhập nên không còn phải ghép lệnh CMD với `Z:\5D Mark III Upgrade\...`. Có thể nhập đường dẫn có dấu cách, có hoặc không có dấu ngoặc kép bao ngoài.

**Cài ExifTool đúng cách (KHÔNG cài vào Canon):**

1. Tải Windows ExifTool 64-bit từ https://exiftool.org/ rồi giải nén.
2. Trong thư mục giải nén sẽ có `exiftool(-k).exe` và một thư mục phụ `exiftool_files`.
3. Đổi tên `exiftool(-k).exe` thành `exiftool.exe`.
4. Chép **CẢ HAI** vào thư mục `tools` nằm cùng cấp với `preflight.py`. **Không chỉ chép file exe**: bản Windows mới cần cả `exiftool_files`. Nếu máy đã cài ExifTool vào PATH, có thể giữ nguyên cài đặt đó.
5. Mở CMD và chạy `tools\exiftool.exe -ver` từ thư mục chứa `preflight.py` để kiểm tra. Nếu hiện số phiên bản thì chạy lại `QVFILM_START_WIN10.cmd`.

Ví dụ ảnh anh đã nhập:

```text
Z:\5D Mark III Upgrade\Photo\_C2A8994.JPG
```

Khi hỏi ổ thẻ, nhập `G:\` nếu muốn kiểm tra sự hiện diện của các file; hoặc **nhấn Enter** để bỏ qua, vẫn kiểm tra metadata ảnh như bình thường.

Lưu ý: Bản v0.2.0 trước đó có thể đã tạo báo cáo `REVIEW_REQUIRED` do thiếu ExifTool. Chạy lại bản v0.2.1 sẽ tạo báo cáo mới tại `reports\qvfilm_preflight_report.json`. Bản v0.2.1 vẫn **không chứa file cài firmware Canon** và không ghi lên thẻ.

---

## 1. Những điều cần biết

Dòng `9.0.1 A6(34)` trong ảnh màn hình máy của anh nhiều khả năng là phiên bản **MPU nội bộ**, **không phải** tên phiên bản Canon firmware công khai. Bảng đối chiếu cộng đồng tại https://github.com/exiftool/exiftool/issues/399 ghi nhận Canon **1.2.3 ↔ MPU 9.0.1/A6**. Đây là bằng chứng hỗ trợ, **chưa được xem là xác minh độc lập để cài firmware**.

**Không cài, không hạ firmware, không chép module thử nghiệm QVFIL lên thẻ đang hoạt động.** Gói này không chứa `.FIR`, `autoexec.bin` hoặc `.mo`.

## 2. Chuẩn bị một ảnh gốc chụp bằng 5D Mark III

1. Lắp thẻ nhớ, dùng chính Canon 5D Mark III chụp **một ảnh JPG hoặc CR2 mới**.
2. Chép **file gốc nguyên vẹn** từ thẻ sang Windows 10. Không dùng ảnh chụp màn hình, ảnh qua Messenger, ảnh đã xuất lại hoặc xóa metadata.
3. Tải **ExifTool cho Windows** từ https://exiftool.org/ . Đổi tên `exiftool(-k).exe` thành `exiftool.exe`, đồng thời đặt **cả `exiftool.exe` và thư mục `exiftool_files`** trong thư mục `tools` của gói (hoặc thêm vào PATH). ExifTool không đi kèm gói QVFilm.
4. Cần có Python 3 trên Windows 10.

## 3. Chạy chương trình trên Windows 10

Giải nén gói vào thư mục trên máy tính, rồi nhấp đúp `QVFILM_START_WIN10.cmd`. Chọn chức năng:

- **1 — Kiểm tra firmware:** nhập đường dẫn đầy đủ đến ảnh JPG/CR2 gốc; có thể nhập đường dẫn ổ thẻ như `E:` để kiểm tra sự hiện diện của file Magic Lantern. Chương trình tạo `reports/qvfilm_preflight_report.json` trên **máy tính**, không ghi lên thẻ.
- **2 — Sao lưu thẻ đang hoạt động tốt:** nhập đường dẫn ổ CF/SD và đường dẫn một **thư mục đích chưa tồn tại** trên PC (ví dụ `C:\QVFilm\5D3\known_good_20261101`). Chương trình chỉ chép `autoexec.bin`, `ML/` và `ML-SETUP.FIR` nếu có. Nó không chép `DCIM/` — cần sao lưu ảnh và video riêng.
- **3 — Kiểm tra bản sao lưu:** đối chiếu SHA-256 mọi file với `BACKUP_MANIFEST.json`. Chỉ chấp nhận bản backup có `BACKUP_COMPLETE.txt`.

Những tác vụ này chỉ đọc thẻ rồi ghi file trên PC. Không tạo thẻ boot, không thay đổi cờ boot (bootflag), không format hoặc cài firmware.

Lệnh nâng cao (không bắt buộc):

```powershell
py -3 preflight.py scan --photo "C:\Photos\IMG_0001.CR2" --card "E:\." --out "reports"
py -3 preflight.py backup --card "E:\." --dest "C:\QVFilm\5D3\known_good_20261101"
py -3 preflight.py verify-backup --dir "C:\QVFilm\5D3\known_good_20261101"
```

## 4. Hiểu kết quả

| Kết quả | Ý nghĩa | Cho phép cài QVFIL? |
|---|---|---|
| `PASS_METADATA` | Ảnh gốc có metadata ghi rõ 5D Mark III và firmware Canon 1.2.3 | **KHÔNG**, cần các vòng nghiệm thu khác |
| `REVIEW_REQUIRED` | Thiếu thông số, thiếu ExifTool hoặc chỉ thấy MPU 9.0.1/A6 | **KHÔNG** |
| `BLOCK_MISMATCH` | Sai thân máy, sai phiên bản 1.2.3 hoặc các trường metadata mâu thuẫn | **KHÔNG** |

Ngay cả `PASS_METADATA` cũng **không chứng minh** gói `autoexec.bin` / module thử nghiệm đã tương thích, máy có bootflag phù hợp, hoạt động ổn định hoặc quay 3K liên tục.

## 5. Phương án dự phòng và khôi phục

- **Trước mọi thử nghiệm sau này:** Giữ nguyên thẻ Magic Lantern **đang hoạt động tốt** (nếu đã có), sao lưu nó ra PC và kiểm tra SHA-256; sử dụng **một thẻ khác** dành riêng cho các bản thử nghiệm. Không được dùng bản thử nghiệm để thay thế thẻ tốt.
- Nếu máy bị treo sau khi lắp thẻ thử: tắt nguồn, đợi đèn ghi thẻ ngừng sáng rồi lấy **thẻ thử** ra. Khi máy đã tắt, có thể tháo/lắp lại pin; thử bật **không có thẻ**. Chỉ trở lại thẻ tốt nếu thân máy hoạt động bình thường. Nếu máy vẫn không khởi động khi không có thẻ, dừng thử nghiệm và tìm hỗ trợ Canon/kỹ sư Magic Lantern có kinh nghiệm.
- Nếu quay RAW bị dừng, có dropped frames, lỗi MLV, nóng bất thường: ngừng quay thử, giữ nguyên file chứng cứ, quay lại bản ổn định. Không dùng máy đã hack cho cảnh không thể quay lại.
- **Quan trọng:** Bản backup SHA-256 chỉ chứng minh file được sao chép nguyên vẹn. Không bảo đảm đây là thẻ khôi phục boot được; bootflag hỏng có thể không sửa được bằng tháo thẻ.

Gói **không tự động khôi phục bằng cách ghi lên thẻ**. Việc làm thẻ boot/installer phải có quy trình riêng, đã đối chiếu chính xác firmware và được nghiệm thu trước khi dùng.

## 6. Những tiêu chí bắt buộc trước phiên bản cài lên máy

1. Xác minh độc lập thân máy đúng 5D3 và firmware Canon 1.2.3.
2. Giữ thẻ boot tốt và có backup file cùng hash.
3. Kiểm tra đúng installer/build tương thích với thẻ và bootflag.
4. Nghiệm thu các nút điều khiển, menu Movie + QVFIL, LiveView và thoát menu.
5. Kiểm tra thực tế RAW 3K 24/25p: nhiệt độ, card speed, dropped frames và thời lượng ghi.
6. Có cách trở về bản ổn định đã kiểm chứng — **không hứa có thể cứu mọi lỗi bootflag**.

## 7. Quyền riêng tư

Báo cáo chỉ lưu tên file ảnh, SHA-256, model và những trường phiên bản firmware được đọc. Không xuất số serial, tên chủ máy hoặc GPS. Ảnh gốc không bị sửa và không tải lên Internet. **Không đăng ảnh cá nhân hoặc báo cáo riêng tư lên GitHub công khai.**

Mã nguồn và bài test có tại https://github.com/hackrockx-apps/magiclantern-qvfilm-5d3 . Chạy test với `py -3 -m unittest discover -s . -p "test_preflight.py" -v`.

**Trạng thái: OFFLINE QA ONLY — NOT FOR INSTALLATION.**