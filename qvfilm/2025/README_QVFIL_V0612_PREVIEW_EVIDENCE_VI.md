# QVFIL v0.6.12 – Preview Lab Render Evidence (5D3.123)

## Hardware finding: 03 Nov 2026

The operator photographed Magic Lantern > Movie with QVFIL **v0.6.10** displayed in the Cinema HUD row, and `Color large STBY` selected while the status said `STBY: N/A`. This is **not proof that v0.6.11 was booted**. v0.6.11 code would display `QVFIL v0.6.11` and a specific gate reason rather than generic N/A. There may be an older module on the active ML card or the camera may still be booting the 0.6.10 build; no attempt should be made to attribute preview performance to v0.6.11 until version is verified.

The operator also submitted four LCD photos:
- Auto: large color preview.
- Real-time: centered smaller colored Canon LiveView.
- Framing: large color preview.
- Frozen LV: large preview in still image.
Static photographs cannot confirm preview FPS or the underlying rendering path. Earlier user observation: Auto/Framing/Frozen update slowly while Real-time feels smooth. Already-recorded MLV files were reportedly opened successfully in MLV App.

## What v0.6.12 really changes

The previous `QVFIL_LAB_STBY` status and `DRAW Xms` could reflect eligibility without evidence of a completed draw. v0.6.12 adds a **session-only counter incremented after the existing `raw_preview_fast_ex` returns, only when `qvfilm_lab_active` is true**.

Menu `Movie → QVFIL Color Lab`:
- `SAFE OFF`: user has not enabled the optional feature.
- Existing specific guards from v0.6.11: `RAW OFF`, `MOVIE LV`, `SET 1X LV`, `LOWER RES`, `SET 10-BIT`, etc.
- `ARMED 0F`: safety gates are met but **no completed color-preview draw** has been observed since the counter reset. Not a PASS.
- `F:N Xms`: N completed draws observed; X ms duration of the most recent render call. Neither number means FPS.
- `REC: BASE`: during RAW recording the original Magic Lantern RAW preview path takes over.

Version visible in Movie → Cinema HUD should read `QVFIL v0.6.12`. If it says v0.6.10 or v0.6.11, the latest module is not loaded; **stop testing and identify which SD/CF card actually supplies `ML/MODULES/MLV_LITE.MO`**. Do not reflash firmware or modify the known-good card.

## Kept unchanged

- Recorder `raw_video_rec_task()` and lossless `compress_task()` are tested byte-for-byte unchanged.
- All frame queues, FIO/card writes, raw DMA, clock/timing and Canon firmware untouched.
- Existing `raw_preview_fast_ex`, its color/gray selection and adaptive preview pacing logic untouched **except the small post-call telemetry counter**.
- Existing 5D3.123 guards, RAW 10-bit <=1600×900 and standby-only gate remain.
- Lab setting volatile, OFF on each boot; 14-bit Lossless remains blocked.
- No attempt to upscale the Canon YUV buffer or to promise full-screen 25fps color.

## Independent acceptance after exact-source CI / ARM build PASS

1. Keep the hardware-PASS v0.6.6 card unchanged. Use the separate backed-up test card and confirm module SHA-256 before testing.
2. Boot the test card and photograph the Movie menu: `QVFIL v0.6.12` is mandatory. If different, STOP: installation mismatch.
3. Set RAW 1280×720 / 10-bit uncompressed / 25fps, Preview Real-time, lens MF, LiveView x1; no REC yet.
4. Select `Movie → QVFIL Color Lab → Color large STBY` (an entry at the Movie menu level, NOT a submenu inside Cinema HUD).
5. Exit menu and view a static bright colorful scene in standby for several seconds; return to Movie and photograph the row. A rising `F:N` and measured `Xms` proves calls happened, not that color or frame rate is good.
6. Compare Auto/Real-time/Framing/Frozen only in standby. Record separate notes on image size, color, response to camera movement, and whether F increases; avoid interpreting LCD as proof of MLV quality.
7. If responsiveness is poor or any UI corruption appears, turn Lab OFF or power-cycle. Do not begin recording with an unverified preview. The already-tested MLV recorder is more important than the monitoring experiment.
8. Only after standby stability and rollback check may a **5–10s 10-bit uncompressed** recording be attempted on test media, followed by MLV App review. During REC `REC: BASE` is expected.

## Proposed next development

A genuine Canon YUV upscaling / hybrid monitor would require inspecting the actual on-camera YUV/VGA buffer geometry, strides, aspect ratio and display callbacks, and measuring CPU load before writing to bitmap or DMA buffers. The four still photos alone are insufficient. Do not silently crop or scale the recording path.

**Current decision:** `V0610_PHOTO_CONFIRMED`, `V0611_ON_CAMERA_NOT_PROVEN`, `V0612_DIAGNOSTIC_SOURCE`, `V0612_HARDWARE_PENDING`, `LOSSLESS14_BLOCKED`.

## 5D3 Movie menu readability

The photographed v0.6.10 menu showed text collisions between the long item name and the selected value. v0.6.12 deliberately shortens **only UI labels** to `QVFIL Color Lab` and `Color STBY` (instead of `QVFIL Color Preview Lab` and `Color large STBY`). The underlying OFF/ON numeric option and the guarded RAW renderer are unchanged. Camera acceptance must use the new name; searching for the old name would be misleading.
