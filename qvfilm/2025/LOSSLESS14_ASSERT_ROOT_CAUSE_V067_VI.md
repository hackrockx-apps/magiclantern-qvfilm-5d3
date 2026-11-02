# QVFIL v0.6.7 — 14-bit Lossless ASSERT: source-level diagnosis only

Date: 2026-11-02
Target: Canon EOS 5D Mark III / Magic Lantern 5D3.123
Pinned source: \`reticulatedpines/magiclantern_simplified\`
Pinned commit: \`ed3e7c0dfacfdeaf3349dee73edf9e3621217462\`
Source file: \`modules/raw_video/mlv_lite/mlv_lite.c\`
Source blob SHA: \`7c0da7cddbf7fba31592eee6b6f4c8964ce1a3a9\`

## Current camera milestone

- v0.6.6 Cinema Slim is now **USER HARDWARE PASS**, confirmed by the operator on 02/11/2026.
- v0.6.6 exact-source tests and 5D3.123 ARM build passed GitHub Actions #45 and #46.
- Preserve the working v0.6.6 card/configuration as the known operational state.
- This v0.6.7 branch is **source diagnosis and test design only**. It does not build a module, change a camera card, or enable lossless.

## What the ASSERT actually tells us

The ASSERT log says:
- \`mlv_lite.c:2742\`, task \`compress_task\`
- Magic Lantern \`2025-06-20.5D3.123\`, commit \`ed3e7c0df\`
- Free memory \`234K + 3897K\` (one report says +3900K)

The exact pinned source confirms line 2742 is the generic \`ASSERT(0)\` in this branch:

\`\`\`c
if (compressed_size < 0 && !RAW_IS_IDLE)
{
    printf("Compression error %d at frame %d\\n", compressed_size, frame_count-1);
    ASSERT(0);
}
\`\`\`

Therefore, the immediate trigger is **a negative return from \`lossless_compress_raw_rectangle()\`**, not the earlier output-pointer alignment assertions or \`CreateMemorySuite\` assertion. The ASSERT log itself does not preserve the preceding printf, so it does not identify the negative code or frame number.

## Three negative return paths in the exact 2025 source

File: \`modules/silent/lossless.c\`, function \`lossless_compress_raw_rectangle()\`.

| Return | Exact condition | Meaning |
|---|---|---|
| \`-1\` | \`!TTL_ResLock || !lossless_sem || !TTL_Start\` | Lossless encoder prerequisites are not initialized/available |
| \`-2\` | \`take_semaphore(lossless_sem, 1000)\` returns non-zero | Encoder completion callback did not signal within 1000 ms |
| \`-3\` | \`WR1_Address\` exists but first output word is not \`0xC4FFD8FF\` | Output does not have the expected JPEG lossless marker/signature |

The code path also:
1. Calls \`TTL_SetArgs(0, &TTL_Args, 0)\`.
2. Configures width/height and EDMAC channels.
3. Sets source/destination addresses and 5D3 DIGIC 5 encoder registers.
4. Calls \`TTL_Prepare\`, registers \`LosslessCompleteCBR\`, sets flags and starts the encoder.
5. Waits on the semaphore for 1000 ms, calls \`TTL_Stop\` / \`TTL_Finish\`, then checks the JPEG signature.

This narrows the investigation substantially, but **does not yet prove which of -1/-2/-3 occurred on the user's camera**.

## Why we must not simply remove the ASSERT

The MLV writer expects a valid compressed frame and slot size. If a negative size is allowed to flow into \`shrink_slot()\` / \`frame_fake_edmac_check()\` and the writer, it can corrupt the MLV or memory state. The original QVFIL patch explicitly contains the 5D3 lossless path before entering the recorder; that is a containment guard, not a compressor repair.

Do not:
- remove the 5D3 lossless guard;
- suppress \`ASSERT(0)\` and continue writing;
- force \`compressed_size\` to a positive size;
- alter TTL firmware addresses or DIGIC registers by guesswork;
- repeat the 14-bit lossless test merely to collect the missing error code;
- enable 3K/lossless, overclock SD/CF, change bootflag or flash Canon firmware.

## v0.6.7 work scope

This milestone is deliberately limited to:
- static source verification of the ASSERT branch and the three return codes;
- an automated regression test against the exact pinned source;
- a reviewable diagnostic design for a later, separate test-only build.

No camera module is produced in this branch. No source is changed in \`mlv_lite.c\` or \`lossless.c\`.

## Next diagnostic design (not implemented here)

Before any controlled lossless experiment, a separate review must decide how to capture:
- return code (-1/-2/-3);
- frame index;
- current resolution/crop and RAW mode;
- whether \`TTL_ResLock\`, semaphore and function pointers are initialized;
- encoder completion timing and output marker;
- whether the failure occurs on the first frame or after sustained capture.

Any future instrumentation must fail closed: on a compression error, stop the recording through a proven safe path and never submit a malformed frame to the MLV writer. This requires source review and tests before considering a camera build.

## Existing safety gate

A prior compatibility audit recorded that the Canon public firmware version was not independently verified, the exact boot card/recovery state was not documented, and the decision was \`HOLD_NOT_APPROVED\`. v0.6.6 hardware PASS is new evidence that the current setup boots and runs the module, but it does **not by itself prove the public Canon firmware version or establish a recovery image**. Reconcile that audit before distributing any new camera module.

## State

- \`V066_CINEMA_SLIM_USER_HARDWARE_PASS\`
- \`V066_EXACT_SOURCE_TEST_PASS\`
- \`V066_ARM_BUILD_PASS\`
- \`V067_SOURCE_DIAGNOSIS_ONLY\`
- \`V067_NO_CAMERA_MODULE_BUILT\`
- \`LOSSLESS14_BLOCKED\`
