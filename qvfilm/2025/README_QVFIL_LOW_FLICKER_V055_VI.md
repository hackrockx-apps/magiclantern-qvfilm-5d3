# QVFIL Cinema Low-Flicker v0.5.5 — Canon 5D Mark III

## Operator evidence (2026-11-02)

QVFIL v0.5.4 experimentally installed on Canon EOS 5D Mark III. Operator provided photograph: **HUD rendered successfully** at 1600×900, 10-bit RAW, ISO 800, 25 FPS, status STBY. The camera can start recording with the rear START/STOP button. During recording, **the LCD LiveView image appears to shake/jitter** (operator could not attach a phone recording). The attached photograph only proves HUD works while idle; it cannot prove frame drops, tearing frequency or whether saved MLV is defective. Upper and lower QVFIL strings visibly conflict with original Canon/Magic Lantern status fields.

## Analysis

In the exact 2025 `mlv_lite.c` source patched by v0.5.4, `qvfilm_draw_cinema_overlay()` was called from `raw_rec_polling_cbr()`, acquiring `BMP_LOCK` and filling **two 672×30px opaque areas** as often as once per 250ms, **even while recording RAW**. That is ~40,320 bitmap pixels redrawn per invocation, up to 161,280 pixels/sec plus text writes and lock activity. Canon/ML graphics can redraw asynchronously. Such a pattern is a **plausible** cause of flicker/visual instability; it is not conclusive without camera recording comparison.

Note: `mlv_lite` and Canon may use non-WYSIWYG preview paths while RAW recording independently of QVFIL. Even with HUD OFF, the user may see a changing preview; therefore compare *HUD ON vs OFF* on the exact same scene and inspect the saved MLV.

## Code changes in experimental v0.5.5

- Retain 2025 source pin `ed3e7c0dfacfdeaf3349dee73edf9e3621217462`, ML model `5D3.123`, QVFIL Enter Cinema and existing Movie + RAW menu.
- `Cinema overlay` mode ID **2** remains unchanged from v0.5.4, so the saved preference maps to the new low-flicker behavior after reboot. OFF and Info bars modes remain.
- Use cached parameters: `STBY/ARM/REC/END`, whole FPS, resolution, RAW output bit depth (BPP) and ISO; repaint on state/settings change. In idle, a periodic recovery repaint is at most once per 5 seconds (not 4Hz).
- Draw compact 475×26px top and 570×26px bottom strips **inside** the video area at y=85 and y=382, away from Canon status lines. Does not remove Canon overlays or change display mode.
- On the **first transition to RAW REC**, paints a small red `REC` label once. Thereafter, **no QVFIL bitmap writes** while `RAW_IS_RECORDING` remains true. Native Canon/ML status stays in control. The QVFIL indicator may be overwritten during recording—this is an intentional performance compromise for this experimental build.
- `Movie → QVFIL HUD Diagnostics` includes Gate=7 meaning intentional bitmap freeze during sustained REC. This is not a crash or module failure.
- No changes to RAW frame/EDMAC buffers, codec, storage, Canon shutter handler, module boot flags or ROM. 14-bit lossless **still blocked due to prior compress_task ASSERT**, not repaired.

## Acceptance gates

1. Keep untouched stock Magic Lantern 2025 SD and private ROM backups. Use the already bootable test card; save current v0.5.4 MLV_LITE.MO first.
2. Only after test and ARM build PASS, verify GitHub artifact SHA-256 and install v0.5.5 **on test card only**. No firmware update, no bootflag rewrite.
3. Boot and confirm `QVFIL v0.5.5` in Movie. Keep 10-bit uncompressed 1280×720 25p for apples-to-apples baseline; RAW ON, Rec trigger OFF, Gradual Exposure OFF, Global Draw ON.
4. Select Cinema overlay and Enter Cinema. Confirm `STBY`; rear START/STOP begin 5–10 sec capture and stop. Observe whether LCD jitter decreases. There may be brief/single redraw at mode transition, not repeated while recording.
5. If possible repeat same scene with `QVFIL Cinema HUD = OFF` for 5–10 sec; compare LCD behavior. Observe whether both new .MLV files decode smoothly and whether timestamps/frame count show loss. **If OFF also jitters, issue is not proved to be QVFIL drawing** and likely requires separate RAW Preview diagnosis, not further HUD flash.
6. If no jitter but camera shows overwritten/missing REC label during recording, treat as expected v0.5.5 limitation; QVFIL intentionally prioritizes capture responsiveness.
7. If any freeze, failed MLV, assert or error, revert to backed-up v0.5.4 or verified stock module on test card. Do not try 14-bit lossless.
8. Report 2 facts: (a) LCD jitter with HUD ON vs OFF and (b) MLV App playback/frame integrity, instead of only a phone recording.

## Status

- `V055_SOURCE_ARM_BUILD_PENDING` (update after CI)
- `V054_HUD_DISPLAY_PASS`
- `V054_LCD_SMOOTHNESS_FAIL_OPERATOR_REPORTED`
- `V055_CAMERA_RUNTIME_PENDING`
- `14BIT_LOSSLESS_UNRESOLVED_AND_BLOCKED`
