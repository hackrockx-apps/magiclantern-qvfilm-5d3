# QVFIL Cinema Monitor v0.6.3 — Canon EOS 5D Mark III / 5D3.123

## Evidence from user's 2026-11-02 test photos

- User reports v0.6.2 recording 40 seconds and also 1600x900 for 1–3 minutes, manual STOP, with no auto-stop.
- **But both photos show a shortened Movie menu lacking even upstream `RAW video`, plus no QVFIL Enter Cinema / Media Engine / Recording Report.** The LiveView image shows a stock movie `MVI_8996` label. This is consistent with `mlv_lite.mo` **not loaded**, hence the new recording might actually be Canon H.264 rather than RAW; the photographs cannot establish that it created `.MLV` for those runs. Do NOT label the 1–3 minute result as confirmed RAW PASS without an MLV file from that test.
- v0.6.1 had user-confirmed custom menu labels PASS; v0.6.0 was explicitly shown to record an actual `M02_1652.mlv` to CF, manually stopped after >20 seconds and opened in MLV App.

## PRIMARY GATE before installing anything else: module load/RAW detection

1. On the camera, navigate to Magic Lantern's `Modules` tab. Locate `mlv_lite.mo` and confirm `ON`; if OFF, enable it and power-cycle normally. If missing, do not format any media: back up the existing card and verify the `ML/MODULES/MLV_LITE.MO` binary is on the booting card (SD/CF boot card ambiguity).
2. Reopen Movie and ensure both `RAW video` and `QVFIL Cinema HUD` plus `QVFIL Media Engine` appear; confirm module build version in menu. If module is ON but missing from Movie, inspect module's error message via Modules menu and restore known-working v0.6.1 experimental test module as needed. Keep original Magic Lantern stock test card and ROM backups untouched.
3. Only consider a RAW test successful if a **new `.MLV` file** appears on CF and can be opened by MLV App with matching resolution, bit depth, frame count and duration. Canon `MVI_*.MOV` alone is **not** evidence of RAW success.

## v0.6.3 feature scope (optional and isolated)

- Add fourth style to **`Movie → QVFIL Cinema HUD`**:
  - `OFF` (0)
  - `Info bars` (1)
  - `Cinema overlay` (2, preserved from previous)
  - **`Large cinema` (3)**: fonts enlarged (FONT_LARGE) for *actual camera data* — focal length (lens_info.focal_len in mm), aperture (lens_info.aperture in tenths), effective shutter reciprocal (get_current_shutter_reciprocal_x1000), ISO (lens_info.iso or iso_auto). When the lens doesn't report a field, display `--` rather than fabricate information.
- Large exposure values use a single low-coverage overlay at the bottom of the image and a small STBY/REC + FPS panel above; the original Canon upper and lower info bars and original Movie menu are untouched.
- Repaint only when values/style change or at rare idle refresh. **Do not redraw repeatedly while RAW recording**; values may remain frozen on-screen if changed after REC. This protects recording responsiveness on the user's machine, which previously suffered LiveView flicker.
- **`Movie → QVFIL Focus Assist`** is a read-only setup guide. Actual colorized MF focus detection is implemented by **original Magic Lantern `Focus` tab → `Focus Peak`**, with choices `Red` and adjustable `Threshold`. The standard **`Magic Zoom`** option, if present, can be used for critical focus checks. The new QVFIL code does **not** run an additional pixel-processing peaking algorithm, rewrite focus measurements, change lens focus or interfere with native processing.
- To use core Focus Peak: enable **Global Draw**, enter LiveView, preferably switch lens AF/MF to MF, set `Focus` → `Focus Peak` to ON, choose Red, adjust Threshold for scene texture; move focus ring and observe highlighted sharp edges. If peaking disappears during RAW capture, it may be core performance gating: don't force another high-frequency overlay.
- 14-bit lossless compression remains blocked due to prior compressor ASSERT; do not try lossless or 3K as part of the basic acceptance.

## Safe test

1. Preserve working module v0.6.1/v0.6.2 and all card/ROM backups; verify checksum for new ARM module. Use only a separate known-bootable test SD with CF as RAW target. **Never flash Canon firmware or modify bootflag**.
2. Confirm `mlv_lite.mo ON` and the Movie menu has `RAW video` + QVFIL entries. If not, STOP; it is a module-load issue rather than a HUD placement issue.
3. Set `QVFIL Cinema HUD → Large cinema`, `Global Draw ON`, `Gradual Exposure OFF`, `FPS override OFF`; RAW 1280×720, 25p, 10-bit uncompressed, Rec trigger OFF, Pre-record OFF. Use `QVFIL Enter Cinema` then verify large **mm/f-stop/1/ISO** fields appear with core LiveView.
4. Test native Focus Peak from Focus tab in standby first with manual focus, then a short 5–10s RAW recording; focus dots may be reduced by ML under load. Check whether the UI remains responsive and doesn't visibly stutter. Avoid changing shutter while RAW REC because HUD's rendering is intentionally paused while capturing.
5. Verify `.MLV` stored on CF, matching fps, frame count and intact playback using MLV App. Check 20–30 seconds only after the short test PASS; expand to longer experiments on CF only.
6. If menu disappears, module OFF, camera freezes, error or MLV missing, return to known-good working v0.6.1 and examine module load info before any further changes.

## Limitations & status

`V061_MENU_USER_PASS`, `V060_SHORT_CF_MLV_USER_PASS`, `V062_MODULE_LOAD_UNCONFIRMED`, `V062_LONG_RAW_UNVERIFIED`, `V063_SOURCE_ARM_BUILD_PENDING`, `V063_LCD_HARDWARE_PENDING`, `NO_OVERCLK`, `LOSSLESS14_BLOCKED`.

Exact 2025 source pin: `ed3e7c0dfacfdeaf3349dee73edf9e3621217462`.
