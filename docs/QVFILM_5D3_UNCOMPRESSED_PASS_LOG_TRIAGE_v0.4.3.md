# QVFilm — Canon 5D Mark III MLV RAW: Uncompressed Control PASS (v0.4.3)

## Operator-confirmed test

Camera: Canon EOS 5D Mark III, installed Magic Lantern **2025-06-20.5D3.123**.

1. Following a prior \`ML ASSERT at mlv_lite.c:2742 (compress_task)\`, the operator powered the camera off and back on normally, no boot freeze.
2. Turned RAW Video OFF, power-cycled, and confirmed normal operation.
3. Re-enabled stock \`mlv_lite.mo\` and tried the conservative **uncompressed RAW** format for 3–5 seconds.
4. The camera did not show an assert and did create an \`.MLV\` file.

**PASS limited to a short uncompressed MLV file creation without on-camera error.** The operator has not supplied the MLV file itself, MLV App decoding results, frame-count analysis, write-speed evidence, ISO, exact resolution and bit-depth after the switch. Do not claim 1080p continuous RAW or 3K readiness.

## Root cause assessment

- Strong differential evidence: the lossless code path had an assertion while uncompressed was able to record a short clip. This narrows investigation to the JPEG lossless path or its interaction with the precise shooting conditions.
- In source \`modules/raw_video/mlv_lite/mlv_lite.c\` commit \`ed3e7c0df\`, line **2742** triggers \`ASSERT(0)\` when \`lossless_compress_raw_rectangle\` returned a negative integer during recording.
- \`modules/silent/lossless.c\` returns \`-1\` (not initialized), \`-2\` (timeout), \`-3\` (unexpected JPEG signature). The error number for the actual failed recording is **unknown until crash/diagnostic logs are examined**.
- Camera previously showed ISO 2000 in the old assert screenshot, and ML's menu source advertises 14-bit Lossless JPEG at very low recommended ISO; this is a hypothesis to assess later, **not proof that ISO caused the problem**.
- A log stored in SD/CF root is not necessarily invalid: different log producers/builds use different paths. Do not move, rename, delete or edit the source logs until copied to a PC.

## Privacy / logs

The user mentioned sending card-root log files, but **no new LOG/TXT files were available in the chat attachment list at this checkpoint**. No claim that any log has been read or an error code recovered.

Safe capture:
1. Power the camera OFF and wait for the card write LED to stop.
2. Copy **only relevant text log files** from the card root and/or \`ML/LOGS\` into a PC folder such as \`Z:\5D Mark III Upgrade\ML_LOG_DIAGNOSTICS\`.
3. Retain the original files and file timestamps. **Do not share ROM0.BIN / ROM1.BIN**, serial numbers or private media publicly.
4. Review the log locally; search for \`Compression error -N at frame X\`, \`mlv_lite.c:2742\`, \`ASSERT\`, and \`compress_task\`.
5. Use \`qvfilm/preflight/triage_ml_logs.py\` on a PC copy if desired:
   \`\`\`powershell
   py -3 triage_ml_logs.py --folder "Z:\5D Mark III Upgrade\ML_LOG_DIAGNOSTICS" --out "Z:\5D Mark III Upgrade\ML_LOG_DIAGNOSTICS_REPORT.json"
   \`\`\`
   This writes a JSON summary with line numbers and codes (not raw log contents), and **does not read from or write to a card**.

## Next safe acceptance steps

A. **Validate uncompressed test on PC**: copy \`.MLV\` to PC, open with MLV App, verify reported resolution, bit depth, 25p, actual duration, image content, export a short sample and look for corrupted/duplicated/skipped frames. Header/file existence alone is not validation.

B. **Preserve lossless crash evidence**: gather user-supplied logs from the SD/CF card root. No need to force another crash or re-enable 14-bit lossless while log analysis is pending.

C. **Avoid re-flashing**: do not use \`Firmware Update\` again, do not replace working stock \`mlv_lite.mo\` with the experimental QVFIL module compiled from a different branch.

D. **Continue RAW scaling only after stable data**: if uncompressed MLV decodes normally, test longer low-resolution clips with known card speed, then use suitable CF UDMA 7 for Full HD recording. Solve lossless crash before 3K experiments, as 3K can require specialized readout and recording module support.

## Status

\`MLV_UNCOMPRESSED_SHORT_RECORDING_PASS_USER_ATTESTED\`

\`MLV_DECODE_INTEGRITY_PENDING\`

\`MLV_LOSSLESS_COMPRESSION_FAULT_REMAINS_OPEN\`

\`RAW_3K_AND_QVFIL_CUSTOM_MODULE_NOT_READY\`
