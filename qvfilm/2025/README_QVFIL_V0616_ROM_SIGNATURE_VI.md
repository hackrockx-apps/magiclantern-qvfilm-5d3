# QVFIL v0.6.16 — Canon 5D3.123 READ-ONLY ROM Signature Diagnostic

## Camera field result v0.6.15

Images IMG_5388.JPG and IMG_5389.JPG show:

- `Cinema slim HUD → QVFIL v0.6.15`: version correctly loaded.
- `QVFIL ID Probe → M:5D3`: camera model property confirmed.
- `QVFIL ID Probe → FW:9.0.1 A6(3` (the display shows only the first 10 characters, likely further characters after this; **not the public Canon firmware menu version**).
- `QVFIL Color Lab → OFF / SAFE OFF`: correct; no display Lab activation.
- Previous `ID 0/0 D5` was due to the `is_camera("5D3","1.2.3")` runtime comparison; `is_camera` uses `PROP_FIRMWARE_VER` string, so it legitimately fails when property is not `1.2.3`.

**This is not proof that the Canon ROM is wrong; do not reflash Canon firmware.**

## Why a ROM signature?

Pinned Magic Lantern 2025 source commit `ed3e7c0dfacfdeaf3349dee73edf9e3621217462`:

- `src/propvalues.c`: `is_camera(model,version)` compares `__camera_model_short` and `firmware_version`.
- `src/propvalues.c`: `firmware_version` is the `PROP_FIRMWARE_VER` callback string.
- `src/reboot.c`: `cstart()` checks firmware ROM signature before ML is allowed to boot.
- `src/fw-signature.h`: `SIG_START = MAIN_FIRMWARE_ADDR`, `SIG_LEN = 0x10000` **uint32 words**, `SIG_5D3_123 = 0x672EEACE`.
- `platform/5D3.123/Makefile`: `MAIN_FIRMWARE_ADDR = 0xFF0C0000`.

The sum reads 256 KiB of fixed, mapped firmware ROM **once when the exact menu item is selected**, without writing to it. This mirrors the boot checksum and is **not** used to bypass the Lab in v0.6.16.

## v0.6.16 change

- Adds `Movie → QVFIL ROM Check`, a read-only one-shot check.
- First confirms `is_camera("5D3","*")` (the compile-time camera model, any firmware property) and `get_digic_version()==5`. Otherwise says `TARGET FAIL / NO SCAN` and does not touch ROM.
- Does not scan while merely scrolling through Movie. Highlights item to scan once per boot/session.
- Compares sum to **0x672EEACE**.
- Displays `ROM:672EEACE / SIG PASS`, or `ROM:<other> / SIG FAIL`.
- Keeps `QVFIL ID Probe` unchanged with `M:5D3` and actual `FW:...`.
- Keeps `QVFIL Color Lab OFF` and the strict 5D3.123 gate unchanged. This is NOT a performance fix.
- Keeps original 10-bit RAW recorder, MLV writer, compressor, camera clock, preview bitmap, BMP functions, EDMAC and FIO unchanged. Module computes a read-only sum only if user selects the diagnostic entry.
- Lossless 14-bit remains blocked.

## Test acceptance

1. Preserve known-good 5D3 ML card. Prepare a backed-up separate TEST card, do not change firmware or autoexec.bin.
2. After CI pass, replace only `ML/MODULES/MLV_LITE.MO` on TEST.
3. Boot and confirm Movie `Cinema slim HUD → QVFIL v0.6.16`.
4. Confirm `QVFIL Color Lab → OFF / SAFE OFF`. Leave OFF; do not record RAW.
5. Move to `Movie → QVFIL ROM Check`. The first highlight triggers the one-time read of 256 KiB of firmware ROM. Photograph `ROM:...` and `SIG PASS / FAIL`.
6. Photograph `Movie → QVFIL ID Probe` for `M:...` and `FW:...`.
7. If `SIG FAIL`, `TARGET FAIL`, lockup, or UI issue, STOP: revert the test card to known-good. Do NOT bypass gate or reflash camera.
8. Even if SIG PASS, **do not enable Color Lab in v0.6.16**. We must update its target check in a separate review (only after on-camera firmware identity evidence, no ungrounded inference).

## Diagnostics versus recording

QVFIL ROM Check is entirely distinct from recording validation; passes do NOT prove Color Preview performance, color reproduction, MLV integrity, or continuous 1080p stability. Past hardware-PASS MLV should be preserved until deliberately retested.

**Release status: source/CI candidate; not camera tested.**
