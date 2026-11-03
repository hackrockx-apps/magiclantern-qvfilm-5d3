# QVFIL v0.6.11 — STBY Color Preview Lab gate fix

Target: Canon EOS 5D Mark III, Magic Lantern 2025 source pinned to
\`ed3e7c0dfacfdeaf3349dee73edf9e3621217462\`.

## Confirmed source-level cause

In v0.6.10, \`QVFIL_LAB_STBY\` required both:

- \`PREVIEW_AUTO\` or \`PREVIEW_CANON\`
- The existing RAW Preview setting was Auto or Real-time.

But \`raw_rec_should_preview()\` already checks \`QVFIL_LAB_STBY\` before its
normal Preview-mode branches and returns \`1\`, deliberately routing the image
through the existing ML RAW display filter. The Preview-mode requirement was
therefore redundant and could reject Framing/Frozen LV even though the Lab was
designed to override the selected preview path. This is a source-level route
to the reported \`STBY: N/A\`; it does not prove which camera setting was active
during the user's test.

## v0.6.11 changes

1. Remove only the redundant \`PREVIEW_AUTO || PREVIEW_CANON\` condition.
2. Add explicit \`raw_video_enabled\`, \`lv\` and \`is_movie_mode()\` checks to the
   active predicate so the menu status and display-filter gate agree.
3. Replace generic \`STBY: N/A\` with a specific diagnostic:
   - \`5D3.123 ONLY\`
   - \`REC: BASE\` / \`RAW BUSY\`
   - \`RAW OFF\`
   - \`MOVIE LV\`
   - \`SET 1X LV\`
   - \`NO RAW SIZE\`
   - \`LOWER RES\`
   - \`SET 10-BIT\`
   - \`RAW INFO WAIT\`
   - \`DRAW Xms\`
   - \`CHECK GATE\`
4. Keep strict safety gates: 5D3.123, Movie LiveView, RAW enabled, recorder
   idle, 1x display, 10-bit uncompressed output, native sensor RAW 14-bit,
   and resolution no larger than 1600x900.
5. Keep the Lab session-only and OFF after reboot.

## Explicitly unchanged

- \`raw_rec_update_preview()\` and its existing \`RAW_PREVIEW_COLOR_HALFRES\`
  renderer and adaptive STBY pacing.
- \`raw_video_rec_task()\`, \`compress_task()\`, RAW slots, writer queue,
  EDMAC/capture path, FIO/card writes and MLV file structure.
- The lossless RAW block for 5D3.123.
- Cinema HUD, Focus Assist and existing diagnostics.

This is a targeted gate/diagnostic fix, not a new full-resolution color decoder
or a promise of 25 fps. The DIGIC 5 preview remains subject to the existing
Magic Lantern color-half-resolution renderer and its measured draw time.

## Build and safety status

The v0.6.10 logs supplied by the user show that v0.6.10 compiled, but that does
not validate camera runtime behavior. v0.6.11 must pass the exact-source
regression tests, 5D3.123 core build and MLV Lite module build in CI before its
review artifact is considered.

No camera binary is included in this source change. The known-good camera
card must remain untouched. If CI succeeds, test the review module on a
separate backed-up TEST card only; do not flash Canon firmware.

## Camera acceptance sequence after CI PASS

1. Keep the known-good v0.6.10 card unchanged; prepare a separate TEST card.
2. Confirm Movie mode, LiveView ON, RAW video ON, 10-bit uncompressed,
   1600x900 or smaller, 1x LiveView, and RAW recorder IDLE.
3. Enable \`Movie → QVFIL Color Preview Lab → Color large STBY\`.
4. Check the status. If it does not show \`DRAW Xms\`, follow the exact
   diagnostic instead of guessing.
5. Test each Preview selection (Auto, Real-time, Framing, Frozen LV) while
   still in STBY. The Lab should no longer reject a selection solely because
   it is Framing or Frozen LV.
6. Confirm color, image area, latency and manual focus behavior. Do not assume
   a particular frame rate.
7. Only after STBY passes, make a 5–10 second 10-bit uncompressed RAW test on
   the TEST card. During REC, expect \`REC: BASE\` and the original preview path.
8. Open the MLV in MLV App and verify frames. Then extend to 1–3 minutes only
   after the short test is clean.

If any display corruption, hang, unexpected flicker or MLV integrity issue
appears, set the Lab to OFF or power-cycle. Do not test 14-bit lossless.
