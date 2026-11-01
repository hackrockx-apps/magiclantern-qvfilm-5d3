# QVFilm 5D Mark III — Seven ASSERT logs / lossless RAW gate (v0.4.4)

## Original field evidence — seven user uploads

Received \`ASSERT00.LOG\` through \`ASSERT06.LOG\` (each 334 bytes). Files were inspected as original data; the repository does **not** commit the private log files or ROM dumps.

- **All seven** point to \`ML ASSERT: 0\` at \`mlv_lite.c:2742 (compress_task)\`, task \`compress_task\`, \`lv:1 mode:3\`.
- **All seven** identify \`Magic Lantern version: 2025-06-20.5D3.123\` and Git commit \`ed3e7c0df 2025_release_01\`.
- **Six files are byte-for-byte identical** (ASSERT00, 01, 03, 04, 05, 06); ASSERT02 differs only in free memory **\`234K + 3900K\` instead of \`234K + 3897K\`**.
- There are thus **2 distinct log contents** across 7 files. This does **not** establish either two or seven distinct crash events.
- No \`Compression error -N at frame X\` or other numeric lossless return code is present in any log. \`ML ASSERT: 0\` is the failed assertion expression, **not** a lossless return code 0.
- The logging occurred at the card root according to the user. It is valid to examine these wherever the running build writes them; do not force moving them to \`ML/LOGS/\`.

## Exact source correlation (installed commit, not the QVFIL fork)

\`modules/raw_video/mlv_lite/mlv_lite.c\` at \`ed3e7c0df\`:
- Calls \`lossless_compress_raw_rectangle()\` in \`compress_task\`.
- If \`compressed_size < 0 && !RAW_IS_IDLE\`, prints \`Compression error %d at frame %d\`, then invokes \`ASSERT(0)\` at line 2742.
- The user logs capture the ASSERT but not the print. Absence of the print in ASSERT logs does not tell us which return code occurred.

\`modules/silent/lossless.c\` defines:
- \`-1\`: lossless encoder not initialized
- \`-2\`: compression completion semaphore timed out
- \`-3\`: compressed output lacks expected JPEG signature

**Current cause category: \`LOSSLESS_NEGATIVE_RETURN_UNKNOWN\`.** No basis to claim damaged sensor, card speed, a specific timeout, or hardware repair requirement.

Source:
- https://github.com/reticulatedpines/magiclantern_simplified/blob/ed3e7c0df/modules/raw_video/mlv_lite/mlv_lite.c#L2730-L2743
- https://github.com/reticulatedpines/magiclantern_simplified/blob/ed3e7c0df/modules/silent/lossless.c

## Positive controlled comparison

Operator reports that after normal power cycle and disabling RAW, a **short 3–5 second RAW uncompressed** recording succeeded and produced an \`.MLV\`, with no on-camera ASSERT. This is **user-confirmed file creation PASS** only: the resulting clip has not yet been uploaded for decoding, full frame count, bit depth or timestamps verification.

This comparison narrows the issue toward lossless-specific processing or its interactions, but does not prove that the uncompressed pipeline is reliable for longer takes, Full HD or 3K.

## Next operational gate (no camera firmware patch)

1. **Keep both original ROM backup and known-working baseline card untouched.** Preserve the 7 original ASSERT files and the test MLV.
2. Open a PC copy of the successful MLV in [MLV App](https://mlv.app/). Confirm readable frames, metadata (resolution, FPS, bit depth), full clip duration, export and no clear corruption. If frames skip, preserve evidence and halt escalation.
3. Determine which exact CF/SD media wrote the test MLV, and its model/capacity/real sustained write speed before deciding on Full HD RAW. Short low-res uncompressed does not prove 1080p throughput.
4. **Do not repeatedly trigger the 14-bit lossless ASSERT.** A future debug build that persists the negative error code requires source-level review/recompilation on the exact 2025 build and isolated hardware validation, not just changing \`ASSERT(0)\`.
5. Do not copy the older fork's custom QVFIL module onto the 2025 baseline card. QVFIL Dashboard/3K stays gated.

## Updated diagnostic utility

\`qvfilm/preflight/triage_ml_logs.py\` (PC-only) now groups identical log hashes and clearly distinguishes file counts from distinct crash events. Its result can say \`ERROR_CODE_NOT_CAPTURED\`, which is expected for these seven logs. It never writes to camera cards, changes bootflags or embeds actual log text in JSON.

**Checkpoint statuses**
- \`STOCK_CANON_AND_ML_BASELINE_PASS\`
- \`MLV_UNCOMPRESSED_3_TO_5_S_RECORDING_USER_PASS\`
- \`SEVEN_ASSERT_LOGS_REVIEWED_TWO_UNIQUE_CONTENTS\`
- \`LOSSLESS_ERROR_NUMBER_UNKNOWN\`
- \`MLV_APP_DECODE_AND_FRAME_INTEGRITY_PENDING\`
- \`3K_AND_CUSTOM_QVFIL_MODULE_HOLD\`
