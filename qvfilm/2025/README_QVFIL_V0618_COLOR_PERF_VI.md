# QVFIL v0.6.18 — Color Preview Performance Telemetry, not a speed fix

## Nghiệm thu v0.6.17 qua IMG_5392.JPG, IMG_5393.JPG, IMG_5394.JPG

- Camera Movie menu shows `QVFIL v0.6.17`.
- ROM check prints `ROM:672EEACE / SIG PASS` and ID Probe shows `M:5D3` with `FW:9.0.1 A6(3...`.
- `QVFIL Color Lab → Color STBY`; first status `ARMED 0F` and subsequent `F:u 209ms`.
- On `F:u 209ms`, the Color Lab draw counter must be greater than zero because source enters that branch only when `qvfilm_preview_lab_draw_count != 0`. But on this Magic Lantern compact menu formatter `%u` was rendered as `u` instead of showing the count.
- **209 ms is the duration of ONE completed existing RAW color preview conversion, not measured presentation FPS.** Even if that time were consistent, 209 ms alone implies a raw-conversion ceiling around 1000/209 = 4.78 conversions/s before waiting and other processing. This is a conditional performance bound, not a measured preview rate.
- `QVFIL Preview Guide → Frozen LV` is shown. Preview Guide is informational; color Lab in v0.6.17 is not restricted to the Preview mode selector.
- **No LiveView image screenshot or video was supplied in this batch**, so color accuracy, framing size and fluidity after enabling the Lab are not hardware-verified.

## v0.6.18 source changes

- Fix QVFIL Color Lab `F:%u` (not supported reliably by the camera menu formatter) to `F:%d` with explicit conversion and saturation at `INT_MAX`, leaving the underlying unsigned draw counter intact.
- Add STBY-only telemetry in the existing preview drawing task, immediately after `raw_preview_fast_ex` returns:
  - Exponential (1/8) average of conversion duration `AVG:xxxms`
  - Exponential (1/8) average of wall-time interval between completed conversions; displayed as approximate `Hz:x.y` in `Movie → QVFIL Color Perf`
- The first draw has no completed period measurement; the menu shows `Hz:WAIT` until the next valid period.
- These are **conversion completion cadence** estimates, not measured LCD refresh or MLV recording fps.
- No extra tasks, buffers, codec operations, memory allocations, firmware/ROM writes, or changing color conversion algorithm.
- Keep `QVFIL Color Lab` OFF by default, and the manually selected `ROM Check → SIG PASS` + exact model/DIGIC5 + RAW enabled/idle/Movie LV/1x/10-bit/<=1600x900 gates unchanged.
- When RAW REC begins the Lab still bypasses to upstream preview. RAW recorder `raw_video_rec_task`, compressor `compress_task`, core preview filter `raw_rec_update_preview` remain byte-identical to v0.6.17.

## Camera acceptance after CI PASS

1. Use **backed-up separate TEST card**, leave known-good card untouched. Replace only `ML/MODULES/MLV_LITE.MO`. No Canon firmware, bootloaders or `autoexec.bin` changes.
2. Confirm `Cinema slim HUD → QVFIL v0.6.18`.
3. Keep `Color Lab → OFF / SAFE OFF` on boot. Set RAW 1280x720, 10-bit uncompressed, 25fps, Movie LiveView 1×, not recording.
4. Select `Movie → QVFIL ROM Check` and confirm `ROM:672EEACE / SIG PASS`; otherwise stop.
5. Select `QVFIL Color Lab → Color STBY`. Leave menu, hold a colorful **static** scene for ~10 s, then gently pan once. Do not record.
6. Return to menu and take photos of `QVFIL Color Lab` with **numeric** `F:<count> <last_ms>ms`; and `QVFIL Color Perf` with `AVG:<ms>ms`, `Hz:<x.y>`.
7. If `F:u` persists, screenshot also `QVFIL v0.6.18`; this would be new formatting regression or wrong module. If `F:0` with color selected, inspect gate status.
8. Observe whether the LCD color and preview framing are usable, rather than relying solely on numbers. If severe lag, freezing, temperature increase, REC behavior changed, or menu crash: switch Lab OFF or reboot and return to known-good.
9. **Do not press REC in this round.** A separate staged MLV recording test only after STBY stability acceptance.

## Future optimization hypotheses (NOT in v0.6.18)

- Bottleneck likely in `raw_preview_color_work()` (Magic Lantern core RAW color-halfres), currently labelled "pretty slow" in `src/raw.h`. It is not enough to shorten the idle sleep.
- Future v0.6.19 may investigate lower-cost demosaic / tile update / selective color or Canon YUV viewport re-mapping, but only after actual conversion cadence and LCD appearance are measured.
- Large + smooth + color preview on DIGIC5 is an engineering target, not yet demonstrated.
