# QVFIL Media Engine v0.6.0 — nghiệm thu CF/SD trên Canon EOS 5D Mark III

## Mục tiêu và phạm vi

Chốt nền: Magic Lantern 2025-06-20, commit `ed3e7c0dfacfdeaf3349dee73edf9e3621217462`; máy mục tiêu 5D3.123; bản QVFIL nền v0.5.6. Đây là **bản đo thụ động và tư vấn băng thông ghi RAW**, chưa phải công cụ tăng tốc bus hoặc sửa driver lưu trữ.

Người vận hành đã báo thẻ **SanDisk Extreme CF 64GB UDMA7** quay khoảng 20 giây 1600×900/25p mà không tự ngắt. Thẻ **Lexar SDXC GOLD 128GB UHS-II V60** từng tự dừng khoảng 11 giây với `Flushing buffers...` khi quay RAW. Bằng chứng này ưu tiên so sánh **trên cùng máy** chứ không sử dụng tốc độ công bố của thẻ làm tốc độ thực tế của khe.

## Thành phần v0.6.0 đã viết

1. Kế thừa `Movie → QVFIL Storage Check` (A: CF / B: SD, lưu lượng RAW ước tính, Last: BUFFER/WRITE) và `QVFIL Cinema HUD` dạng low-flicker.
2. **Movie → QVFIL Media Engine**: chỉ đọc, xác định chính đích ghi MLV theo mã gốc (`get_cf_dcim_dir()`), tính nhu cầu **MiB/s** từ độ phân giải, RAW bit depth và FPS. So sánh với quan sát từ **phiên ghi MLV thật gần nhất** trên cùng ký tự ổ; cảnh báo nếu throughput theo thời gian phiên ghi thấp hơn 120% nhu cầu. Đây là **ngưỡng cảnh báo thận trọng**, không phải cam kết về tốc độ ổn định.
3. **Movie → QVFIL Recording Report**: hiển thị `Flow` (MiB/s dựa vào dữ liệu đã ghi / thời gian phiên quay), `I/O` (MiB/s dựa vào thời gian gọi FIO_WriteFile của mã nguồn gốc), thời lượng phiên, **số entry còn chờ trong writing queue khi dừng** và mã lỗi BUFFER/WRITE/NONE. Không đánh đồng số entry còn chờ với số frame bị hỏng.
4. Bộ đếm này lấy timestamp ở `RawRecTask` **sau khi file MLV được tạo thành công**, chụp tổng byte ghi, tổng thời gian writer và backlog tại lúc dừng **trước khi flush**. Không tự tạo file benchmark, không lặp đo mỗi frame, không sửa bit depth, không ép tốc độ bus.
5. Cơ chế dừng khi buffer đầy, nhánh abort/flush và chốt khóa 14-bit lossless vẫn như v0.5.6. Không thêm `sd_clock`, SD overclock, Dual Card Spanning hoặc firmware flash.

## Giới hạn phép đo

- `Flow` chỉ là **dòng dữ liệu đã đi tới file trong khoảng thời gian ghi**. Khi buffer tồn đọng, số này thấp hơn nhu cầu; nó không đo chính xác tốc độ tối đa của thẻ.
- `I/O` chỉ dựa vào thời gian FIO của tác vụ ghi MLV (không gồm mọi overhead của máy).
- Đổi sang thẻ vật lý khác cùng ký tự ổ có thể làm kết quả cũ không còn đại diện; bộ đo chỉ nhận diện A/B, **không có fingerprint CID/serial**. Muốn nhận diện thẻ mới cần quay clip mới.
- Quan sát 20–30 giây **không bảo đảm quay liên tục 3 phút**. Mỗi lần khởi động lại máy, các số liệu RAM không được giữ lại (sau reboot sẽ cần đo mới).
- Con số trên nhãn SanDisk 120 MB/s chủ yếu là tốc độ đọc tối đa, không phải hiệu suất ghi liên tục đã xác minh.

## Cách nghiệm thu an toàn

1. Giữ nguyên thẻ SD Magic Lantern 2025 đã PASS, bản sao ROM*.BIN và module v0.5.6. Dùng **thẻ thử có thể khởi động**, sau khi sao lưu module cũ và SHA256. Không chạy Canon Firmware Update.
2. Gắn CF SanDisk Extreme UDMA7 nếu đã sao lưu nội dung. Trong Canon chọn CF làm đích ghi cho tác vụ chung khi phù hợp. Mở `QVFIL Storage Check`, xác nhận **A:**. Chỉ dựa trên menu hoặc thư mục MLV sau khi ghi, không suy luận từ thẻ chứa Magic Lantern.
3. `Movie → QVFIL Cinema HUD` chọn OFF để giảm chồng chéo khi đo; RAW ON, 1280×720/25p/10-bit uncompressed, Rec trigger OFF, Gradual Exposure OFF, FPS override OFF, Pre-record OFF. `QVFIL Media Engine` trước quay phải báo `NOT TESTED`.
4. Thoát hẳn menu bằng ERASE hoặc `QVFIL Enter Cinema`, nhấn START/STOP ghi 20–30 giây; dừng bằng START/STOP và **đợi flush hoàn tất**.
5. Vào `QVFIL Recording Report`: chụp Flow, I/O, thời lượng, pending queue, stop. Vào `QVFIL Media Engine`: chụp Need, Obs và cảnh báo. Các số đo mang tính chẩn đoán, không phải benchmark chuẩn về tốc độ CF.
6. Xem file .MLV mới trên CF; dùng MLV App để xác minh đủ frame và không có corrupt frame; sau đó thử 1600×900 ở 25p từ 30 giây đến 3 phút với cùng trình tự. Nếu tự ngắt, ưu tiên lưu báo cáo và file thực tế trước khi chuyển chế độ.
7. Với thẻ SD Lexar, không thử 1600×900 25p dài trên khe SD 5D3 mặc định. Có thể thực hiện một phép thử ngắn tại RAW 960×540 để lấy phép đo so sánh; cần sao lưu dữ liệu, vì tính năng ghi giới hạn SD chưa được khắc phục.
8. Nếu máy nóng bất thường, treo, hiện ASSERT, đóng băng hoặc có MLV hỏng, dừng nghiệm thu, khôi phục module gốc trên thẻ thử. Không bỏ qua các nhánh an toàn khi buffer đầy.

## Roadmap riêng (không thuộc v0.6.0)

- v0.6.x: đánh giá performance trên CF, chẩn đoán frame integrity, cân nhắc điều chỉnh chế độ GUI ít xung đột.
- Nhánh nghiên cứu độc lập SD Overclock: module `modules/sd_clock/sd_uhs.c` tồn tại ở nhánh phát triển mới, có code dành riêng cho 5D3 1.2.3 với mức 160/192/240 MHz. Đó là module **thử nghiệm ở mức register/driver**, có nguy cơ mất quyền truy cập thẻ SD khi lỗi. Không ghép binary hoặc source trực tiếp sang bản ML 2025 đang quay tốt mà không kiểm tra ABI và phục hồi.
- Card Spanning CF+SD không được bật: cần thiết kế writer, rollback và khả năng phục hồi MLV riêng; chưa có kiểm chứng thực tế trên máy người dùng.

**Các nhãn trạng thái:** `SOURCE_TEST_PENDING`, `ARM_BUILD_PENDING`, `CAMERA_RUNTIME_PENDING`, `OVERCLOCK_DISABLED`, `LOSSLESS14_GUARDED`. Cập nhật thực tế sau CI và thử nghiệm.
