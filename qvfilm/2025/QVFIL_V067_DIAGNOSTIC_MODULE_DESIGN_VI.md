# QVFIL v0.6.7 — Lossless diagnostic module design (pre-build gate)

Date: 2026-11-03
Target: Canon EOS 5D Mark III, public firmware 1.2.3 / Magic Lantern 5D3.123
Known-good camera state: QVFIL v0.6.6, user hardware PASS
Scope: design and host-side verification only. This document does not authorize a camera install.

## Operator recovery update

The operator reports that a full backup of the SD/CF card(s) currently running Magic Lantern has been created. This upgrades the recovery status from "backup not reported" to "full-card backup reported". The project has not yet independently verified the backup's byte size, SHA-256, readability, or restore/boot test. Preserve the original v0.6.6 card untouched.

Canon firmware 1.2.3 is user-confirmed. Do not update to Canon 1.3.3 or later; Canon states that 1.3.3+ cannot be downgraded to 1.2.3:
https://www.cla.canon.com/en/support/product-advisories/adv-eos5d-markiii-miscpage

## Exact failure path established from pinned source

Pinned upstream: `ed3e7c0dfacfdeaf3349dee73edf9e3621217462`.

In `modules/raw_video/mlv_lite/mlv_lite.c`, `compress_task` calls `lossless_compress_raw_rectangle`. A negative result during recording currently prints the error and calls `ASSERT(0)`. The subsequent normal path deletes the memory suite, evaluates size, may shrink the slot, invokes the fake EDMAC check, and marks the slot full. Those latter steps must never run for a negative result.

The normal recorder has an existing `buffer_full` abort path in `raw_video_rec_task`. However, simply setting this flag in the compression task is NOT YET PROVEN SAFE: the affected slot has already been inserted into the writing queue as `SLOT_CAPTURING`, and the recorder's early-stop/flush code must be audited to ensure it cannot wait forever, assert, or write that invalid slot.

## Diagnostic contract — mandatory before C instrumentation

1. Capture a single immutable diagnostic record: signed return code, frame index, output mode/BPP, resolution/crop, whether the failure happened during active recording or idle probe, and a compact stage code.
2. No printf flood, heap allocation, file I/O, UI drawing, or blocking semaphore operation in the compressor task.
3. On `compressed_size < 0`, do not call `shrink_slot`, `frame_fake_edmac_check`, or mark the slot `SLOT_FULL`.
4. Request recorder termination through a reviewed state transition. The recorder must drain or explicitly discard the failed slot and every later queued slot without writing malformed VIDF data. It must close/finalize the MLV safely if possible, then expose a clear "LOSSLESS ERROR — RECORDING STOPPED" result.
5. Preserve the original `ASSERT` behavior until the stop/queue contract is proven in source and host tests. Never silently suppress the ASSERT and continue.
6. The diagnostic must be read-only with respect to camera firmware, boot flags, card layout and Canon settings.

## Error taxonomy

- `-1`: prerequisites unavailable (`TTL_ResLock`, semaphore, or `TTL_Start`).
- `-2`: encoder completion semaphore timed out (1000 ms).
- `-3`: output does not begin with expected lossless JPEG marker `0xC4FFD8FF`.

Do not assume any one code is the user's historical failure; the old ASSERT logs did not retain the preceding diagnostic printf.

## Implementation sequence

- **D1 — host model:** implement a small host-side state model for valid compression, negative return, queue ownership, abort request and finalization. Test that a failed slot can never transition to writer-eligible `SLOT_FULL`.
- **D2 — source audit:** trace all queue and slot transitions from `process_frame` through `compress_task` and the `abort_and_check_early_stop` path. Identify a bounded cleanup path for the failed slot and queued frames.
- **D3 — test-only C patch:** only after D1/D2 pass, add bounded telemetry and a fail-closed abort. Keep 14-bit Lossless disabled by default and behind an explicit diagnostic-only compile-time switch.
- **D4 — compile + static review:** cross-compile for exact 5D3.123 source, inspect map/size, verify no other camera target is changed, verify 10-bit uncompressed path is byte-for-byte unchanged.
- **D5 — staged camera test:** only after backup checksum/readability and a documented restore procedure are confirmed. First test diagnostic module with Lossless OFF and existing 10-bit uncompressed workflow. Do not intentionally reproduce the 14-bit crash until the fail-closed queue handling is independently reviewed.

## Current decision

`V066_KNOWN_GOOD_PRESERVED` / `CANON_FW_1_2_3_USER_CONFIRMED` / `FULL_CARD_BACKUP_OPERATOR_REPORTED` / `BACKUP_INTEGRITY_AND_RESTORE_NOT_YET_VERIFIED` / `V067_HOST_MODEL_AND_QUEUE_AUDIT_NEXT` / `NO_CAMERA_MODULE_BUILT` / `LOSSLESS14_BLOCKED`.
