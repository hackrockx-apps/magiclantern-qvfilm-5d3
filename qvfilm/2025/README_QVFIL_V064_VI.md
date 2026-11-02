# QVFIL v0.6.4 — Canon EOS 5D Mark III / 5D3.123

## Hardware acceptance: v0.6.3 — 02 November 2026

Operator reports successful 1920x1080 RAW capture for 4 minutes, manually stopped, with a valid .MLV opened and visually checked (no apparent missing image). Evidence is **USER PASS**; the original .MLV was not provided to independently verify dropped-frame counts or every decoded frame. Photograph shows REC at 00:39, 32 C, 25 fps; the four-minute total is the operator's report, not the photographed timer.

Movie menu photos show v0.6.3 module loaded, all QVFIL items present, RAW video ON 1920x1080 1.00x. The user has NOT yet validated the Large cinema HUD or the Focus Peak overlay: Cinema HUD is OFF and HUD diagnostics shows Draws:0 / Gate:1 (normal for OFF).

CF estimates from photographed menu: RAW Need=61.7 MiB/s, active FIO I/O=68.4 MiB/s, Flow=61.7 MiB/s. Estimated headroom=(68.4/61.7-1)*100=10.9%, below the 20% caution threshold. Active writer I/O is NOT a sustained-card-speed benchmark; four-minute user success is encouraging but does not guarantee unlimited runtime. Bit depth is not directly shown in the photograph.

Previous v0.6.2 user PASS: 1600x900 3 minutes with playable MLV. Keep user's known-good v0.6.3 card intact.

## Change scope: v0.6.4

- New Movie > QVFIL Shoot Check READ-ONLY entry: current resolution / bit depth / fps; estimated CF I/O margin versus current theoretical RAW payload demand based on previous capture's active writer I/O.
- Explicit warnings for RAW OFF, blocked lossless compression, target not CF, no prior sample, last buffer/write failure, <30s sample and estimated margin under 20%.
- Better Cinema HUD menu help: OFF / Draws:0 / Gate:1 means disabled; enable Large cinema and Global Draw then use Enter Cinema. Large mode can cache displayed values during RAW REC to avoid flicker.
- Existing focus assist remains read-only setup help for native Magic Lantern Focus > Focus Peak (Red and Threshold). It is NOT a Blackmagic focus algorithm or automatic lens actuator.
- Keep all core RAW recording code, file writing, sensor, buffer safety stops, codecs, focus image processing, Canon firmware and SD clocks unchanged. The 5D3 lossless ASSERT remains guarded.
- Exact upstream source: ed3e7c0dfacfdeaf3349dee73edf9e3621217462.
- Test: the raw_video_rec_task body must be identical to v0.6.3; only a conservative menu update is permitted.

## Camera test — only on separate backed-up test boot card

1. BEFORE installing v0.6.4, user can test CURRENT v0.6.3 features: Movie > QVFIL Cinema HUD > Large cinema (currently OFF), enable Global Draw, select QVFIL Enter Cinema; inspect focal length, shutter, f-stop and ISO in standby. Disable HUD if display flickers or overlaps. For manual focus, move physical lens switch to MF and enable core ML Focus > Focus Peak (Red, tune Threshold).
2. Preserve working v0.6.3 SD and all private ROM backups. After successful CI and checksums, copy experimental v0.6.4 MLV_LITE.MO to ML/MODULES on a separate TEST boot card only. No firmware flash, bootflag modification, card overclock, lossless or 3K tests.
3. Confirm Modules > mlv_lite.mo ON, Movie has RAW video plus QVFIL Cinema HUD v0.6.4 and QVFIL Shoot Check. Verify Shoot Check readout and available warning text in the menu, without recording.
4. On test CF, record 5-10s at 1280x720, 25fps, 10-bit uncompressed, Gradual Exposure OFF, FPS override OFF. Manually STOP and inspect fresh .MLV in MLV App.
5. Only if tests PASS, repeat 30 seconds and 1920x1080 for 4 minutes using same known-good capture settings previously tested with v0.6.3. Check decoded MLV and frame drops; record actual stop reason and image stability.
6. If new issue appears, return to original v0.6.3 working card immediately; do not change RAW buffer behavior to mask errors.

STATUS:
V063_MODULE_MENU_USER_PASS
V063_1080P_4MIN_MLV_USER_PASS
V063_LARGE_HUD_NOT_YET_TESTED
V063_FOCUS_PEAK_NOT_YET_TESTED
V063_CF_ACTIVE_IO_ESTIMATED_MARGIN_10P9_PERCENT
V064_SOURCE_ONLY_UNTIL_CI_AND_ARM_BUILD_PASS
V064_CAMERA_TEST_PENDING
LOSSLESS14_BLOCKED
