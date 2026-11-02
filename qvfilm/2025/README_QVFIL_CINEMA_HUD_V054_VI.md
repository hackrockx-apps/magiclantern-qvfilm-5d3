# QVFIL Cinema HUD v0.5.4 — Canon LiveView compatibility

**Device:** Canon EOS 5D Mark III (Magic Lantern dev 2025-06-20 / 5D3.123).
**Source lock:** `reticulatedpines/magiclantern_simplified@ed3e7c0dfacfdeaf3349dee73edf9e3621217462`.
**Previous tested module:** QVFIL v0.5.3 (user report).

## Hardware evidence from operator

The operator has installed v0.5.3, selected `Movie → QVFIL Cinema HUD → Cinema overlay`, and used `QVFIL Enter Cinema`. It closes Magic Lantern's menu and returns to **Canon default LiveView**. Rear START/STOP starts/ends a recording per operator, but neither `STBY` nor `REC` nor the QVFIL overlay is visible.

This means menu exit **worked**, but overlay visibility **failed**. The user did not upload a new MLV here; we do not know whether the latest test captured RAW MLV or Canon H.264. The previously proven RAW pass remains only the 1280×720/25p 10-bit uncompressed MLV decoded in MLV App.

## Source-level root cause hypothesis

The v0.5.2/v0.5.3 Cinema overlay function checked `get_global_draw()`. At this exact upstream revision, `src/zebra.c` returns false when `lv_disp_mode != 0`, even if `get_global_draw_setting()` is ON. The user is seeing Canon's own information LiveView, so v0.5.3's gate could prevent the QVFIL draw entirely. Further, QVFIL was drawn only from inside `show_recording_status()`, which returns early for roughly one second; Canon can update the graphics between its draws. Its background used the deprecated `COLOR_BG_DARK`, aliased to transparent black on this platform.

These are **specific code defects / plausible blockers**, not measured runtime proof. The new diagnostic item can distinguish the remaining blockers if this change still does not display.

## Changes to patch (all confined to `modules/raw_video/mlv_lite/mlv_lite.c`)

- Retain `OFF / Info bars / Cinema overlay` choice, `QVFIL Enter Cinema`, Canon Movie menu, existing MLV recording controls, 10-bit uncompressed baseline.
- In Cinema overlay mode, require `get_global_draw_setting()`, but deliberately **do not require** `get_global_draw()`, allowing opt-in overlay over Canon default LiveView display mode. Still require model 5D3, Movie LiveView, RAW enabled, liveview display idle, Canon menu closed, bitmap palette active (module-safe bmp_is_on).
- Migrate draw to end of `raw_rec_polling_cbr()` (ShootTask), **after** default ML status, instead of gating on the one-second early return inside `show_recording_status()`.
- Throttle painting to at most once per **250ms** (no VSYNC/EDMAC/RAW capture hook). Guard drawing with `BMP_LOCK` and use opaque dark palette `COLOR_ALMOST_BLACK`, not transparent `COLOR_BG_DARK`.
- Top bar: `QVFIL CINEMA v0.5.4`, `STBY / ARMING / REC / ENDING` (REC red), current FPS. Bottom: output resolution, **BPP of actual RAW output**, uncompressed/lossless indicator, ISO. These are all user-configured/recorder state displays, not an altered RAW image.
- Add **read-only** `Movie → QVFIL HUD Diagnostics` with counters `Draws:<n>` and `Gate:<n>`. Gate codes: 0=conditions clear, 1=HUD mode off, 2=not Movie LiveView or RAW off, 3=Global Draw setting OFF, 4=LCD/BMP off, 6=Canon UI not idle. The last LiveView gate remains available when menu is reopened; the menu itself does not overwrite it.
- The v0.5.3 fail-closed guard against broken **14-bit lossless compression** remains. Lossless is still NOT repaired.

## Camera test plan on the previously working *test* card

1. Power down completely; save the v0.5.3 module. Keep the untouched stock 2025 Magic Lantern card and original ROM backups safe.
2. Only after source tests/ARM cross-compile PASS: verify the SHA256 checksum from the GitHub Actions artifact, place the exact v0.5.4 `MLV_LITE.MO` in `ML/MODULES` **on the already-bootable separate test card**. Do **not** reinstall or update Canon firmware.
3. Boot. Movie menu must identify `QVFIL v0.5.4`; Modules should load `mlv_lite.mo` with no errors.
4. Set `QVFIL Cinema HUD → Cinema overlay`, Global Draw ON; RAW video 1280×720/25p **10-bit uncompressed**, Rec trigger OFF, Pre-record OFF; Gradual Exposure OFF. Leave Advanced off.
5. Select `QVFIL Enter Cinema` and press SET. Wait at least 2 seconds, confirm two opaque bars with real STBY, FPS, RAW/ISO and no lingering `Gradual Exposure` menu header.
6. If bars are missing, return to Movie and note `QVFIL HUD Diagnostics → Draws / Gate` **without modifying anything else**. Example: `Draws:0, Gate:3` means GD setting off; `Draws:>0, Gate:0` means the draw function ran, so the failure is downstream in Canon bitmap compositing, not a missing module or callback.
7. If bars are visible, press rear START/STOP once, verify REC red, record 3–5 seconds, stop. Confirm a new **.MLV** (not just .MOV) and play it in MLV App. If it still only produces Canon MOV, RAW acceptance is not established.
8. On any freeze, incorrect bitmap, media error or failure to record, stop. Power off safely and restore previous module or the known-good stock card. **Do not attempt 14-bit lossless or 3K**.

## Release gates

- `v0.5.4_SOURCE_ARM_COMPILE_PENDING` → will update after CI results.
- `v0.5.4_LCD_RUNTIME_PENDING`
- `RAW_10BIT_UNCOMPRESSED_PRIOR_PASS` (1280×720).
- `LOSSLESS14_ASSERT_UNRESOLVED` (still blocked).
- `NO_FLASH_NO_BOOTFLAG_CHANGES`.
