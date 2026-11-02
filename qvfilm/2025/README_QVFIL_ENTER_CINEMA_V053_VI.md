# QVFIL Cinema Overlay v0.5.3 — Enter Cinema LiveView without recording-key confusion

## Symptom observed by operator

5D Mark III, stock Magic Lantern 2025 source with QVFIL v0.5.2 module: Cinema overlay selected, RAW video 10-bit uncompressed ON, Global Draw ON. A menu label `Gradual Exposure ON` is visible across the *top of the image*. Pressing rear START/STOP returns to Magic Lantern's Movie tab instead of showing a confirmed RAW recording.

There is **no new screenshot or MLV file uploaded in this turn**. Do not assume a recording began.

## Diagnosis from exact stock ML source `ed3e7c0df`

- In `src/menu.c`, a menu can be active in **LiveView Transparent Mode**: `menu_lv_transparent_mode=1`. `handle_ml_menu_keys` handles `BGMT_LV` by toggling transparency, and the menu itself is *still active*. This fits the observed `Gradual Exposure ON` text and return to Movie after pressing START/STOP.
- In `modules/raw_video/mlv_lite/mlv_lite.c`, `raw_rec_keypress_cbr` recognizes `MODULE_KEY_LV` or `MODULE_KEY_REC` only if RAW enabled, Movie mode and the LiveView display is idle. The Canon menu handling may intercept the event before recorder handling, so do **not** attempt to grab or synthesize key events.
- Changing `Gradual Exposure` to OFF is a separate operator setting and was **not** automatically performed by v0.5.3.
- This is an actionable hypothesis based on real source and user observations, **not independently proved** without runtime event trace.

## v0.5.3 source implementation

Exactly same Magic Lantern dev source `ed3e7c0dfacfdeaf3349dee73edf9e3621217462` as installed baseline. The patch remains in `qvfilm/2025/apply_qvfilm_patch.py`. The new Movie entries, in order:

1. `QVFIL Enter Cinema`: an **explicit action** invoked by SET. If Movie LiveView and RAW enabled, calls native `gui_stop_menu()` and `lens_display_set_dirty()`, which closes the active Magic Lantern menu rather than leaving a transparent menu awaiting another key. This does **not** start a recording.
2. `QVFIL Cinema HUD`: OFF / Info bars / Cinema overlay.
3. Original `RAW video` and every original Movie tab item remain.

The overlay never overrides Canon LV/AF or start/stop behavior, and runs only while Movie LiveView is idle with Global Draw ON. v0.5.2 bit-depth and red REC status display are retained. 14-bit lossless **still blocked** due to previous `mlv_lite.c:2742` ASSERT; there is no claim of compression repair.

## Runtime acceptance on a spare bootable SD card

1. Preserve the original ML 2025 SD card, ROM backups and v0.5.1/v0.5.2 module copies.
2. Only when exact-source ARM compile PASS, replace `ML/MODULES/MLV_LITE.MO` on the already used **test** SD. Power off, restart to actually load it.
3. Movie tab shows QVFIL HUD `v0.5.3` and `QVFIL Enter Cinema`; do not proceed if version missing.
4. In Movie tab, turn `Gradual Exposure OFF` explicitly, RAW video ON at **1280x720, 25p, 10-bit uncompressed**, Rec trigger OFF, FPS Override OFF. Set HUD to `Cinema overlay` and Global Draw ON. Do not change Advanced settings.
5. Highlight `QVFIL Enter Cinema` and press SET **once**. Magic Lantern menu should *fully close*, not become transparent; `Gradual Exposure` menu label must disappear. If not, use the trash/ERASE button to close ML menu manually and do not press REC until it is closed.
6. Confirm overlay shows `STBY`; press START/STOP once in Movie LiveView. Confirm `REC` state and RAW file recording, then stop after 3–5 sec.
7. Confirm the new MLV file actually exists on the expected SD/CF card and is decodable by MLV App. No success should be inferred from icon transitions alone. 
8. If START/STOP still returns to Movie or Canon information UI, **stop**; do not install another camera module blindly. Record LCD before/after pressing, module state, and any `ASSERT*.LOG`, along with whether a new MLV was created. Revert to stock module if any malfunction.

## Future work

A dedicated full-screen Blackmagic-style UI is not feasible by drawing two info bars alone; it would require a separately profiled on-screen display compositor that coordinates Canon UI overlays, possible HDMI, refresh and performance. Do not force bitmap operations during recording frame hooks or replace Canon firmware.

Status: `SOURCE_PATCH_AND_COMPILE_VERIFICATION_REQUIRED`; `CAMERA_TEST_PENDING`.
