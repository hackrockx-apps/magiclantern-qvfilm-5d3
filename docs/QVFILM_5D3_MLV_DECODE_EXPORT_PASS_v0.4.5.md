# QVFilm 5D3 — MLV RAW decode/export acceptance checkpoint v0.4.5

**Date:** 2026-11-01
**Body:** Canon EOS 5D Mark III
**Installed ML baseline:** development 2025-06-20.5D3.123
**Source evidence:** three operator-provided screenshots (MLV App viewer, MLV App Clip Information, external MOV player). No source MLV or MOV file was uploaded with these screenshots.

## Result

**PASS: short 10-bit uncompressed MLV capture, decode and MOV export** — operator reports normal playback, no visibly corrupt frames, exported MOV opens in player.

The MLV App UI shows clip M01-1602.MLV and the following metadata:

| Field | Observed |
|---|---|
| Camera | Canon EOS 5D Mark III |
| Resolution | 1280 × 720 |
| Frame rate | 25 fps |
| Frames | 293 |
| Duration | 00:00:11 in MLV App (293/25 = 11.72 seconds) |
| Format | 10 bits, uncompressed |
| Size | 322 MB |
| Data rate | 27.48 MB/s (file average as shown by MLV App, **not card benchmark**) |
| ISO | 2000 |
| Shutter | 1/100 sec |
| Lens | EF24-105mm f/4L IS USM |
| Focal length | 80 mm |
| Aperture | f/4 |
| Audio | none |

MLV App status in operator screenshot displays Frame 293/293; the video is visible and operator has independently exported and opened a MOV file. **This does not mathematically prove zero missing/corrupt frames within MLV timestamps**, since only screenshots and visual acceptance were supplied, not the binary streams.

## Prior crash context

Seven ASSERT00.LOG–ASSERT06.LOG files (two unique contents) all show an assert at mlv_lite.c:2742 (compress_task) from the 2025 build; they do not include the actual negative return code from lossless_compress_raw_rectangle. The original failed test used 14-bit lossless, whereas this successful clip is 10-bit **uncompressed**. Thus the working uncompressed test **does not** clear the lossless bug.

The experimental QVFIL UI/module must not be copied onto the current stock Magic Lantern card. The previously built QVFIL code came from another source tree and lacks confirmed module ABI compatibility with the 2025 build.

## Next gate: CF card performance and Full HD RAW (uncompressed only)

Keep an untouched known-working boot SD plus the private ROM*.BIN backups; do NOT reinstall ML or rewrite bootflags.

1. Record SD/CF card **exact manufacturer/model/capacity and speed rating**. Preserve all existing files; do not format any card with photos without separate verified backup.
2. For a clean Full HD test, use a suitable fast CF card and verify it can be selected for recording in the camera. Canon's Record func+card/folder sel. menu under **Standard** allows selection of CF (Record/play); Magic Lantern's actual MLV destination must still be confirmed by inspecting the file location after a 3–5s test. Do not assume changing this setting alone verifies MLV destination.
3. Remain in the stock module mlv_lite.mo, choose 1920x1080 25p, **10-bit uncompressed**, Pre-record OFF, Rec trigger OFF, FPS Override OFF; avoid crop/HDR/high FPS and leave Advanced unchanged.
4. Bandwidth estimate: 1920×1080×10/8×25 / 10^6 = **64.8 MB/s** before alignment/overhead. Target practical sustained CF speed with margin of at least ~80–100 MB/s. Do not infer performance from the card's advertised read speed.
5. First 3–5 second recording; confirm actual MLV is on CF, absence of card write errors, no ASSERT, successful decode in MLV App, frame count/timestamps as expected. Stop after any warning or visible corrupt frame. Then try 15s/30s only after successful short and repeated power-cycle tests.
6. 25p cinematic motion blur typically corresponds to 1/50 s shutter (~180°), unlike observed 1/100 s (90°). This is an aesthetic camera setting, not a fix for the lossless ASSERT. Avoid changes that induce overheating or flicker.
7. Audio remains OFF during codec/storage stress testing and can be validated separately after video passes.

Do not try Full HD **14-bit lossless** again to establish bandwidth. The lossless compression path still asserts, and the exact return code is unknown.

### Beyond Full HD

3K Cinema RAW is a separate high-risk build/feature gate, not an automatic result of 720p success. Review compatible 2025 source/module ABI, documented crop/readout behavior, cooling/power, CF sustained write speed, actual frame drops, playback and recovery. Do not install custom QVFIL until isolated source-compatible QA passes.

## New acceptance labels

- ML_BASELINE_BOOT_AND_CANON_SMOKE_PASS
- ROM_BACKUP_REPORTED_PASS
- MLV_720P25_10BIT_UNCOMPRESSED_RECORD_PASS
- MLV_720P25_MLV_APP_DECODE_USER_PASS
- MLV_720P25_MOV_EXPORT_USER_PASS
- MLV_LOSSLESS_ASSERT_OPEN
- FULL_HD_RAW_CF_NOT_TESTED
- CUSTOM_QVFIL_3K_NOT_APPROVED

## References

- Canon 5D Mark III CF/SD selection: https://th.canon/en/support/8201363400
- ML RAW throughput considerations: https://github.com/arnaud-sintes/Magic-Lantern-documentation
- MLV App: https://mlv.app/

This is a documentation/evidence milestone only. No on-camera code or firmware is altered.
