# QVFIL v0.5.6 — Camera-side RAW recording storage diagnosis (Canon 5D3.123)

## Evidence from user-supplied photographs (2026-11-02)

The user's experimental QVFIL v0.5.5 module ran on Canon EOS 5D Mark III. The device indicated `RAW`, 25 FPS and a red timer `00:07 ~03`; ~11 seconds into the recording it unexpectedly stopped. LCD text:

- `Movie recording stopped automagically`
- `Flushing buffers... 126 frames left` (another capture: 108 frames left).

A still photograph proves that the recorder entered its **early stop + buffer flushing path**. It cannot prove every frame was preserved, or whether the origin was a buffer overflow vs a file I/O error, absent the actual MLV file and last-error event. This is not the former 14-bit lossless ASSERT.

User's photographed media: **Lexar Professional GOLD 128 GB UHS-II SDXC V60**, marketed 280 MB/s read and 210 MB/s write. The advertised write speed requires a compatible SD UHS-II host. Canon confirms the **EOS 5D Mark III's SD slot does not support UHS speeds** (even UHS-I cards revert to ordinary SD-mode speed); a fast Sony camera can reach a different throughput on the same SD card. Official reference: https://sg.canon/en/support/8201558700

Magic Lantern upstream `mlv_lite.c` at source commit `ed3e7c0dfacfdeaf3349dee73edf9e3621217462` uses `get_cf_dcim_dir()` when generating the MLV output filename: it **selects A:/ CF when present**, otherwise the camera's selected card. On-camera boot SD is *not enough* to determine MLV destination. New diagnostic explicitly displays the actual selected MLV destination (A=CF, B=SD on 5D3).

Theoretical uncompressed 10-bit 25 FPS data rates:
- 1600×900: 45.0 MB/s (payload only)
- 1280×720: 28.8 MB/s
- 960×540: 16.2 MB/s
- 1920×1080: 64.8 MB/s
Additional MLV headers, padding and write variation add overhead. Exact operating thresholds depend on each camera/card and should be measured at the MLV destination.

## Code changes in v0.5.6

- Preserve exact 2025 source pin `ed3e7c0df`, QVFIL v0.5.5 low-flicker HUD, menu Movie and 10-bit RAW recording engine.
- New **Movie > QVFIL Storage Check** is read-only: displays active MLV target drive letter and theoretical uncompressed RAW MB/s load based on actual `res_x`, `res_y`, `BPP` and `fps_get_current_x1000()`; reports `Last:BUFFER` or `Last:WRITE` for the latest recording attempt.
- In `raw_video_rec_task`, reset last reason at the start. Set `BUFFER` before the existing `buffer_full` early-stop path; set `WRITE` if `write_frames` fails. The original branches, buffer flush and safe stop are preserved. **No attempt to overrun full memory slots or ignore write errors.**
- The menu explains that a non-CF target is limited by the old camera's SD interface, regardless of the 210 MB/s Lexar label. Warn to use genuine CF UDMA7 for heavy uncompressed RAW; do not assert an unsupported exact maximum bus throughput.
- Theoretical rate is **not** a measured throughput benchmark. Last stop reason is RAM-only, not written to card, and resets on the next recording attempt or reboot.
- **No automatic silent resolution/codec changes.** 14-bit lossless remains blocked due to earlier ASSERT, and may not be presented as fixed.

## Acceptance plan

1. Save current operator's v0.5.5 test card and preserve original stock Magic Lantern 2025 SD/ROM dumps.
2. After exact-source ARM CI builds and SHA256 passes, install experimental v0.5.6 **on isolated test card only**, no Canon firmware updates/bootflags.
3. Movie shows QVFIL version 0.5.6. Open `QVFIL Storage Check` BEFORE another recording. Photograph drive letter `A:` or `B:` and estimated MB/s. If B: (SD) and rate 45.0 MB/s: this is a major foreseeable write-speed mismatch; **do not retest 1600×900/25p uncompressed on this SD card**.
4. Recommended next test: a genuine CF UDMA7 card, with properly backed-up CF contents; install CF while retaining current ML SD as boot media. Verify new Storage Check shows A:. Confirm MLV actually appears in CF/DCIM after short capture.
5. If CF unavailable, use lower recording settings such as 960×540 25p 10-bit uncompressed (16.2 MB/s payload) for a short diagnostic, but this is **not guaranteed continuous recording** without an empirical sustained write test; it does not meet 3K cinema goal.
6. Only after source-backed media is confirmed, record a short 3-5s 1280×720/25p/10-bit uncompressed clip, then 15–30s and open in MLV App, checking frames and timestamps. With good CF, increase to 1600×900 as separate step.
7. If it auto-stops, read `QVFIL Storage Check → Last:BUFFER/WRITE` right after recording (without reboot) to triage memory starvation vs file write failure. Note that a corrupt/dropped frame can still exist even if partial MLV opens.
8. Never disable safe buffer stop, increase frame slot count past physical memory or force camera to keep recording into corrupted frames. Abort any persistent error.

**Camera runtime for v0.5.6 pending.** This is a diagnostic and root-cause-preserving upgrade, not a firmware trick that can accelerate 5D3 SD hardware.
