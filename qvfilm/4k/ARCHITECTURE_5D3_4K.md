# QVFIL 4K Cinema RAW — Canon EOS 5D Mark III / 5D3.123
**Architecture decision record · 2026-11-04 · NO camera binary released**

## Product goal (not just a marketing "4K" label)

1. Capture *native sensor 1:1 crop RAW* at width >=3840; avoid upscaling 1080p or label trickery.
2. **First realistic production candidate:** 3840×1600 at 23.976/24p, ~2.40:1 cinematic frame, subject to *actual* frame metadata, recording duration and integrity verification. This is **not** UHD 3840×2160.
3. **Aspirational UHD:** 3840×2160 24/25fps 10-bit-or-higher lossless RAW, continuous and stable; may be infeasible with DIGIC5 / Canon 5D3 sensor readout, CPU, RAM, storage. DO NOT claim implemented until hardware proves it.
4. Preview must be *color, large enough to focus/frame, responsive during STBY and REC*. LCD itself is low resolution; it does **not** have to show every 4K pixel. Target a usable 15–20+ visually smooth frames per second during REC; **measured**, not inferred from "raw conversion Hz". Hard fail if gray, frozen, severely laggy, misframed or causing frame drops. If preview cannot be smooth and color while recording, 4K Cinema Stable is **NOT DONE**.
5. Preserve functioning 1080p RAW as safe backup and original Canon firmware 1.2.3. Do not touch firmware flash/autoexec on known-good SD/CF card.

## Discovered source architecture

- **Active QVFIL v0.6.20 experimentation**: a separate branch's *source patch* targets `reticulatedpines/magiclantern_simplified` pinned to 2025 commit `ed3e7c0dfacfdeaf3349dee73edf9e3621217462`. Its legacy RAW color conversion on user's real hardware took `AVG:207–208ms` or about 3.4 completions per second, not LCD FPS. Repeating 2/3 stripe experiments has **not** shown 25fps and does not unlock sensor readout.
- **This repository master**: forks Arnaud Sintes' Danne-derived 4K tree. It ALREADY contains `modules/crop_rec/crop_rec.c` with 5D3 1:1 3K, UHD-width and half-rate 4K presets; `modules/mlv_lite/mlv_lite.c` with 4K crop integration, lossless and card spanning; and `src/raw.c` with the cached `raw_preview_fast_ex2` ultrafast preview pipeline.
- Cached preview precomputes RAW pixel offsets/gamma tables. The 5D3 ML menu exposes `Framed preview → Engine: legacy / ultrafast` and idle/recording color/gray and resolution behavior. Core `raw_preview_fast_ex2` has `RAW_PREVIEW_ADAPTIVE` and separate `_recording` state. **No proof these provide smooth 4K on this body yet**.
- **Do not copy the 2025 `MLV_LITE.MO` or v0.6.x source diff into this 4K tree.** They have different core interfaces and ABI. Starting from the coherent full 4K tree is the faster, safer architecture; port the QVFIL cinema HUD as a separate compatibility-reviewed layer only after crop-rec/MLV/preview baseline builds together.
- Only public Canon firmware `1.2.3` confirmed by user; internal `FW:9.0.1 A6(34)` was observed via ML ID probe but does not itself prove wrong Canon firmware. Check exact 5D3.123 target and ROM signature before any camera pilot.

## Hard throughput numbers (minimum theoretical payload, decimal MB/s)

`W × H × fps × effective_bits_per_pixel / 8 / 1,000,000`. Excludes buffering, metadata, filesystem stalls, capture time, encoder load and thermal limits. Use:
`python3 qvfilm/4k/feasibility.py --write-mb-s 100 --headroom .20 --compression 1.0`
The `100` is a hypothetical input, NOT the user's CF speed. Past QVFIL menus displayed `CF Need:28.8 MB/s`, not proof of a sustained 4K card benchmark.

| Mode | Raw 10-bit MB/s | Required compression at 100 MB/s measured write with 20% headroom |
|---|---:|---:|
| 3840×1600 @ 24 | 184.3 | 2.30× |
| 4096×1440 @ 25 | 184.3 | 2.30× |
| 3840×2160 @ 25 | 259.2 | 3.24× |
| 3072×1920 @ 24 | 176.9 | 2.21× |

**Lossless compression ratio varies by scene and ISO.** A hypothetical 2.5× ratio is not a dependable guarantee for continuous footage. **Full 4K UHD cannot be promised by optimizing Preview alone**; there are independent sensor readout, compression and write throughput constraints. This is why choosing a real, existing 4K-width cinema preset is not "1080p renamed".

## Major integrated program — do NOT repeat dozens of small user trials

**Engineering package A (offline, no user interaction):**
- Pin the working Danne/Arnaud 5D3.123 source in this branch, CI compile **core + crop_rec.mo + mlv_lite.mo together**, flag ABI and packaging errors, produce hashes/build manifest.
- Validate current 4K crop registers/preset names against actual MLV resolution and frame-rate semantics in source. Source-label `UHD 1:1` can mean **3840×1600**, not UHD 3840×2160.
- Preserve/restore session-on-boot `preview engine=ultrafast` control from existing module; A/B preview *color vs gray / full vs half* based on actual camera data and only opt-in. Do not patch sensor register tables speculatively.
- Use `qvfilm/4k/feasibility.py` as a hard storage plausibility check; verify source modes and bounds, not invent guaranteed throughput.
- Port QVFIL Cinema HUD, peaking and diagnostics later as minimal isolated overlays, not in the frame capture, codec or I/O fast path.

**Hardware acceptance package B (ONE integrated on-camera test session after offline passes):**
- TEST card only, known-good SD/CF untouched. Never update Canon firmware or autoexec on production card.
- Test known 1080p 10-bit 25fps baseline and one native >3840-width crop mode first to ensure 4K pipeline really exists.
- Compare legacy and ultrafast cached **framed preview** STBY and REC. Judge real LCD framing/color and responsiveness using phone video during pans; the preview's fps counter is not the same as RAW recording fps.
- One 4K-width raw recording of 30 seconds then 2–3 minutes, if buffer/write and temperature permit; inspect MLV metadata, all frame counts, corrupt frames/dropped frames and playback in MLV App; note crop and scene exposure.
- Log sustained CF write on the CAMERA, not the card's label. If MLV backlog increases or card overflows, stop.
- Stop test at first serious display/recording error; restore tested known-good module and card. Never knowingly run an unsafe extended capture.
- Optional **UHD 16:9** only if code, sensor mode and modeled write headroom allow; not a mandatory dangerous experiment.

**Release decision C:**
- `QVFIL 4K Cinema Candidate`: 4K-width 24/25p RAW + usable color preview while STBY/REC, at least 2–3 minutes clean recording, repeated successful MLV decode, and safe shutdown. Only after this hardware PASS.
- `QVFIL UHD 4K`: separate stricter label requiring **actual 3840×2160** 24/25p video (no upscale/crop mislabel), stable recording, color Preview and all above checks.
- If no combination can attain these simultaneously on this hardware, publish **hardware-limited / not achieved** and preserve known-good RAW rather than claim Stable. Do not force memory, CPU, SD-overclock or bypass protection.

## External technical context

- 2017 ML 5D3 proof of concept: 3840×1600 24p and 4096×1440 25p; 4K preview often broken or gray. See DPReview April 2017 & Newsshooter April 2017.
- Arnaud Sintes March 27 2024 release: `crop_rec_4k_mlv_snd_isogain_1x3_presets_ultrafast_fsq_2024Mar27`, both 5D3.113 and 5D3.123, cached ultrafast color/gray framed preview.
- Danne/Arnaud 5D3 technical notes: multi-card spanning/SD overclock can increase bandwidth but also introduce instability; do NOT assume reliable >=145 MB/s.

## Current status

Source/integration preflight only. **NO camera-installable 4K/QVFIL build has been proven**, and no users should replace their existing 1080p module with a single file from this branch until a coherent same-build core and modules have been verified.
