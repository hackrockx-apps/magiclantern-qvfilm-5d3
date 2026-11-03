# QVFIL v0.6.19 – experimental 3-band Color STBY on 5D3.123

## v0.6.18 field acceptance (four uploaded photos IMG_5395–5398)

- Camera loaded `Cinema slim HUD: QVFIL v0.6.18`.
- `QVFIL ROM Check: ROM:672EEACE SIG PASS`.
- `QVFIL Color Lab: Color STBY`; first shows `ARMED 0F`, later `F:2 211ms`.
- `QVFIL Color Perf: AVG:207ms, Hz:3.4`. F and timing now correctly displayed.
- Last screenshot demonstrates two completed RAW color conversion calls, not two seconds or two full frames per second. The Hz estimate comes from the interval of the first valid pair and may NOT represent a stable average of a ten-second run.
- Color visible with a large frame; **no measured LCD refresh rate or proof of smoothness**.

## Analysis of pinned upstream ML2025 raw color converter

- `src/raw.h`: `RAW_PREVIEW_COLOR_HALFRES` labelled "pretty slow".
- `src/raw.c`: `raw_preview_color_work(raw_buffer,lv_buffer,y1,y2)` computes gamma tables, LV-to-RAW X lookup and processes LV Y lines in the supplied `[y1,y2)` interval.
- `src/raw.c`: `raw_preview_fast_ex` supports explicit LV line coordinates. Default `-1,-1` uses `BM2LV_Y(os.y0), BM2LV_Y(os.y_max)`.
- `mlv_lite.c`: original core calls `raw_preview_fast_ex` once per update; capture and full-size buffers are independent of this lab.

## v0.6.19 opt-in experiment

`Movie → QVFIL Color Lab` offers:
- `OFF`: default after every reboot; upstream preview untouched.
- `Color STBY`: v0.6.18 full-height conversion; control/reference.
- `Stripe STBY`: only in strictly gated standby, pass one of three disjoint LV-Y bands per update to the *same* ML core color converter. Adjacent bands follow integer divisions of display height. On third band, count one complete sweep.

New read-only `Movie → QVFIL Color Sweep` reports `C:N` completed three-band sweeps, `B:N/3` next band, or `T:Nms` interval between the last two complete sweeps. A **sweep is NOT a synchronized full video frame**; parts may be different ages and motion may tear or appear to roll. `QVFIL Color Perf` remains the **per-call conversion duration and completion cadence**. During Stripe STBY, `F` counts completed bands, NOT complete frames.

### Guaranteed non-goals and safety

- This is **not a proven speed upgrade**. Smaller bands may reduce blocking latency per call but repeated gamma LUT initialization may make total whole-frame time longer and worsen color motion. No 25fps promises.
- No new allocations or tasks in QVFIL. No new direct memory/EDMAC/ROM writes or capture frame manipulation.
- Nothing changes in `raw_video_rec_task`, `compress_task`, frame buffer writer or MLV format. RAW REC bypasses the Lab, coordinates default `-1,-1` as before.
- Only target on model 5D3, DIGIC5, explicit manually selected `ROM Check SIG PASS`, RAW ON, Movie LiveView 1x, recorder IDLE, 10-bit, native 14-bit raw source, RAW resolution ≤1600×900.
- Keep tested known-good SD/CF card intact; use backed-up TEST card and replace only `ML/MODULES/MLV_LITE.MO`. Do not touch Canon firmware or autoexec.bin.

## Acceptance plan

1. TEST card only. Confirm `Cinema slim HUD → QVFIL v0.6.19`, with `Color Lab → OFF` at boot.
2. RAW 1280×720, 10-bit uncompressed, 25fps, Movie LiveView 1×. `ROM Check → ROM:672EEACE SIG PASS`.
3. Set `Color Lab → Color STBY` (reference). Observe static colorful scene about 10–15 seconds then small slow pan. Photograph LiveView, `Color Perf`, `Color Lab`, `Color Sweep`.
4. Set `Color Lab → OFF`, then `Stripe STBY`. Observe same scene for 10–15 seconds. Photograph equivalent screens. In this mode `Color Sweep` should have `C:N` increasing after each three bands. Read `T:...ms` after at least two completed sweeps.
5. Compare whether the image develops horizontal update seams, changes exposure/color unexpectedly, gets stuck, or slows menus. **Do not record RAW in this acceptance round**.
6. If Stripe mode causes notable lag, tearing, color instability, heat or unresponsive buttons, turn Lab OFF and reboot; if unresponsive, power down and restore known-good test-card module.
7. Provide four screenshots from each mode, including separate LiveView photos without menu overlay. A short recording of the LCD by phone during a pan may help judge apparent motion (not a precise FPS measurement).

**Build status: candidate until exact-source CI + ARM compile PASS. Hardware remains untested.**
