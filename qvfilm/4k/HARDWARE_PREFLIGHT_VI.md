# QVFIL 4K Cinema — Cổng kiểm tra an toàn trước khi thử trên EOS 5D Mark III

**Trạng thái: ENGINEERING / CHƯA PHÊ DUYỆT CÀI LÊN MÁY.**
Tài liệu này là quy trình giảm rủi ro, không phải giấy chứng nhận an toàn hoặc phần mềm ổn định.

## Đã xác minh (04-11-2026)
- Máy Canon EOS 5D Mark III: Canon firmware **1.2.3** (người dùng xác nhận).
- SD 128 GB, tên Windows **EOS_DIGITAL (G:)**, exFAT: thẻ Magic Lantern 2025 đang boot được; sao lưu **78/78 tệp, FAILED=0** vào `Z:\5D Mark III Upgrade\BACKUP_TEST_G_20261104`.
- CF 64 GB SanDisk SDCFXS-064G: camera benchmark **67.9 / 74.7 MB/s**, có `malloc error: buffer=16777216`; **đây là số của CF, không phải SD**.
- Bản pilot trước: SHA-256 19/19, offline staging 19/19 vào `Z:\5D Mark III Upgrade\4K_PILOT_STAGING`; **không** chứng minh chạy được trên máy.
- Có 7 ASSERT log trong Magic Lantern 2025 tại `mlv_lite.c:2742`, `compress_task`; **không suy ra** lỗi đã xảy ra hoặc được sửa trên cây 4K khác.

## Gia cố source cho lần build sau
- RAW recorder, Crop preset, card spanning và More Hacks: OFF theo mặc định.
- **Mới**: tắt thêm `raw.small.hacks`, `raw.use.srm.memory`, `raw.CropRecPreview` mặc định.
- Cố định 10-bit uncompressed làm định dạng mặc định, nhưng chỉ dùng khi lưu lượng phù hợp.
- Test tự động kiểm tra lại tất cả các giá trị này và packaging fail-closed khi anchor không khớp.
- **Rủi ro còn tồn tại:** bật `MLV_LITE.MO` vẫn khởi tạo `lossless_init()` và task `compress_task` ngay lúc nạp module. Không có bằng chứng an toàn hardware. Bản này **không** sửa logic task nén hoặc các thanh ghi cảm biến.

## Cổng H0 — điều kiện bắt buộc trước khi THỬ BOOT
- [ ] GitHub Actions của **commit mới nhất** SUCCESS toàn bộ core 5D3.123 + MLV Lite + Crop REC + unit tests; tải **bản ZIP mới nhất**, không dùng ZIP từ commit cũ.
- [ ] SHA-256 `MANIFEST.json` của ZIP mới và staging cùng commit PASS, không trộn tệp của các phiên bản.
- [ ] Có **thẻ SD/CF TEST bootable độc lập**, không phải thẻ duy nhất đang boot ML ổn định. Không có ảnh/footage quan trọng; đã sao lưu/khôi phục theo kế hoạch.
- [ ] Đã thử máy vào Canon menu bình thường **không lắp card**, có pin đầy, nắp thẻ đóng, môi trường thông thoáng.
- [ ] **Không** dùng bất kỳ `.FIR` nào, không thay bootflag, không định dạng/thay đổi card boot duy nhất, không dùng SD overclock hoặc card spanning.
- [ ] Người thử hiểu rủi ro và có thể dừng nếu máy treo; không coi PASS code/CI là chứng nhận an toàn.

**Chưa đủ bất kỳ dòng H0 nào => KHÔNG chép bản Pilot lên thẻ đang có; không khởi động Pilot.**

## Cổng H1 — BOOT-ONLY (chỉ sau khi H0 hoàn tất và người thử tự chấp nhận rủi ro)
1. Cất thẻ Magic Lantern đang hoạt động tốt. Dùng **thẻ TEST bootable riêng** với bộ `CARD_ROOT` đồng nhất; không trộn module/CFG cũ.
2. Lần boot đầu **chỉ lắp thẻ TEST**, tháo thẻ ở khe khác để tránh boot nhầm phiên bản.
3. Pin đầy; bật máy; quan sát khởi động và menu. **RAW video OFF, Crop OFF**, chưa bật mô-đun nén/crop mới, không REC.
4. Nếu menu hoạt động bình thường, chụp ảnh một màn hình và tắt máy bình thường. Chưa thử RAW hay 4K ở lần khởi động đầu.
5. Nếu treo / nóng bất thường / đèn ghi liên tục / cảnh báo: ngừng; nếu camera không phản hồi, theo quy trình Magic Lantern hãy tắt nguồn, chờ ngừng ghi, tháo pin, **tháo thẻ thử**, lắp lại pin, khởi động Canon **không lắp thẻ**. Không tháo thẻ khi đang ghi; không chạy Firmware Update.

## Cổng H2 — chỉ sau khi H1 PASS
- Nạp module và kiểm tra menu tối thiểu, không bật đồng thời nhiều cấu hình mới.
- Bắt đầu RAW 1080p ngắn, không nén, chỉ nếu tính toán băng thông thực tế đáp ứng.
- Crop `UHD 1:1` nghĩa là **3840×1600**, không phải UHD 3840×2160. Preview đã được chính source chú thích `preview broken`.
- Với CF 74.7 MB/s không thử ghi liên tục 3840×1600/24p/10-bit không nén (~184.3 MB/s). Lossless có thể lỗi hoặc không đủ tỉ lệ nén, cần thử riêng có kiểm soát.
- Bất kỳ ASSERT, mất frame, buffer tràn, nhiệt/preview bất thường => STOP.

**Đây là bộ sưu tập bằng chứng và gate kỹ thuật, không có tuyên bố 4K Stable/4K UHD.**
