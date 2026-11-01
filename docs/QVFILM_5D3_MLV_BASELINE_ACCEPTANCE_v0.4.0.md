# QVFilm 5D3 Cinema RAW — Baseline MLV Acceptance v0.4.0

Status: **Stock Magic Lantern 2025 boot and basic camera checks PASS; MLV not yet tested.**

## Evidence / safety gates

- User reports 6/6 Magic Lantern baseline checks PASS and has backed up \`ML/LOGS/ROM*.BIN\` privately.
- Camera: Canon EOS 5D Mark III.
- Installed Magic Lantern (LCD photos): \`2025-06-20.5D3.123\`.
- First-install card: a dedicated SD card; existing Canon CF/SD cards were kept separate.
- **Do not** overwrite the known-good baseline SD card or copy the QVFIL custom \`mlv_lite.mo\` onto it. QVFIL was compiled from **a different development fork**; its module ABI and recording hooks have NOT been shown to match the 2025 Magic Lantern build.
- The ML install message \`Boot flag is already set\` has been recorded, but this alone does not establish when the camera bootflag was set.
- Basic ML boot/menu/Canon H.264 passes do not verify RAW, SD/CF write speeds, frame integrity, audio synchronization or continuous recording.

## Stage 1 — inspect and activate stock MLV recorder only

1. Use fully charged battery, stock Magic Lantern test SD inserted; mode dial \`M\`, camera in Movie/LiveView mode.
2. Press **ERASE** to open Magic Lantern.
3. Navigate to the **Modules** tab (blocks/grid icon). Photograph the complete module list **before modifying anything**.
4. Confirmed by the camera operator on the stock 2025-06-20.5D3.123 build: the Modules tab lists `mlv_lite.mo`, `mlv_play.mo`, and `mlv_snd.mo`, with **no `mlv_rec.mo`**. This is expected: `mlv_lite.mo` provides MLV RAW recording.
5. Enable **only `mlv_lite.mo`**. Leave `mlv_play.mo` and `mlv_snd.mo` OFF for this first silent recording test. Never import an `mlv_rec.mo` or `raw_rec.mo` from another build.
6. Exit and perform a normal power cycle; verify `mlv_lite.mo` loads without error.
7. Open Movie tab, locate RAW video (MLV) or RAW video. Photograph both main item and its submenu before changes. If absent, stop and diagnose load status; do not copy incompatible modules.
8. Do not invoke Firmware Update, reinstall ML-SETUP.FIR, or reformat the known-good card.

## Stage 2 — conservative short RAW recording

- First test is intentionally short and uses **only settings exposed in the stock module**.
- Start with \`1280x720\`, 23.976/24 fps, if selectable. If the SD-card write indicator says required write speed exceeds measured card speed, **step down to 960x540 or another offered lower resolution, or stop**.
- Leave advanced crop/1:1/high-fps/HDR/pre-record features OFF.
- Use 14-bit RAW if provided. If the build offers lossless compression, choose it only after confirming that exact module's compatibility; no need to modify camera ISO/other sensitive limits.
- For the first test, do not require audio; \`mlv_snd\` can be enabled later if this module version provides it. \`MLV\` on screen is not itself confirmation of audio.
- Exit menu, enter LiveView. Start recording through the assigned normal Record control, stop after ~5 seconds.
- If the camera warns about card write speed, buffer overflow, skipped frames, or recording stops prematurely, stop experimentation and retain error text. Slow SD is a likely cause; **do not compensate by changing firmware or internal registers**.
- On Windows copy the original MLV clip to PC and keep an unchanged backup. Use the optional \`inspect_mlv.py\` offline inspector to verify a file is present, starts with MLV magic \`MLVI\`, and report file size/sha256. This is **not a decodability or dropped-frame check**.
- Use [MLV App](https://mlv.app/) to open/preview the short clip; verify visible complete image and no apparent missing/corrupt frames. Save an export test. A full dropped-frame count requires recorder diagnostics/MLV parser or frame-by-frame checking, not the basic file signature.

## Stage 3 — Full HD RAW on fast CF *after Stage 2*

- 5D Mark III Full HD RAW 1920x1080 at 24 fps 14-bit uncompressed is approximately **87 MB/s** before overhead; 720p is still approximately 39 MB/s.
- The original 5D3 SD slot is much slower than a properly selected UDMA 7 CF card. **An SD-only short test passing does not establish continuous 1080p capability.**
- First inspect whether the camera can **record RAW to CF** while maintaining Magic Lantern startup. Do not assume automatic dual-card routing or that a blank CF card is configured for ML boot.
- Use a verified fast CF card with adequate sustained write speed, then try 1920x1080 23.976/24p for 5–10s, assess frame drops and playback; increase duration only if stable.
- 3K crop RAW is a separate experimental phase, not a property automatically enabled by the stock 2025 build.

## Submit next report

Report:
- **Modules:** Exact name, green/loading status (photo)
- **Movie:** RAW video (MLV) entry and available resolution/bit depth (photo)
- **Storage:** SD card brand/model/size and CF card brand/model/size, if available
- **First MLV:** Settings, number of seconds, file name/size, playback PASS/FAIL, warning text
- **Backup:** Whether the stock ML card has been cloned/its ML files SHA-256 backed up (ROM already backed up)

Do NOT upload private ROM dumps, serial numbers or personal photos to a public repository.

## References

- Canon 5D3 MLV module enable steps: https://www.cined.com/guide-raw-on-a-5d-mark-iii-magic-lantern/
- RAW data & bandwidth overview: https://github.com/arnaud-sintes/Magic-Lantern-documentation
- Working Windows/Linux MLV conversion app: https://mlv.app/

**Gate:** \`STOCK_MLV_MODULE_VERIFIED\` must be achieved before any camera RAW setting advice is finalized. \`QVFIL_CUSTOM_MODULE_INSTALL\` is independently blocked pending the 2025 build ABI comparison and hardware sandbox testing.
