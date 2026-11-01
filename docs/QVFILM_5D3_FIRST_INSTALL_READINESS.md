# QVFilm Magic Lantern — First-install readiness (Canon 5D Mark III)

**Status: INSTALL BLOCKED.** This document records the first-install prerequisites. It is **not** an installation procedure, a recovery card or a firmware update.

## Evidence from 2026-11-01 field audit

The user's QVFilm Compatibility Audit v0.2.2 reports:

| Evidence | Actual finding | Interpretation |
|---|---|---|
| Camera body | `Canon EOS 5D Mark III` | Model confirmed by original photo metadata |
| Internal MPU | `9.0.1 A6(34)` | Community report links it to firmware 1.2.3. Not a formal attestation of actual public Canon firmware |
| Firmware target | `5D3.123` | Candidate only |
| `card_status.status` | `NO_ML_FILES` | None of the expected files found on the **inspected path** |
| `ML/` | Not found | Does **not** prove Magic Lantern was never installed on another card |
| `autoexec.bin` | Not found | Inspected card is not an identified working ML boot card |
| `bootable_verified` | False | No successful boot test reported |
| `installation_decision` | `HOLD_NOT_APPROVED` | No new firmware or module should be put on the camera |

MPU mapping provenance: https://github.com/exiftool/exiftool/issues/399 . The cited report says "5D III 1.2.3 (9.0.1) A6", but its author collected examples from a third-party camera tool. No original Canon firmware version of 1.2.3 has been observed independently on **this** body.

## Next physical gates (in this order)

1. **Identify the inspected card:** Check Windows File Explorer to ensure the drive letter points to the actual 5D Mark III CF/SD card. Seeing `DCIM` alone does not prove it is the correct card; check the card label and known photos. Do not format it. If it is simply a regular Canon card, `NO_ML_FILES` is expected.
2. **Determine whether Magic Lantern was already installed:** With the camera OFF and no pending writes, use the same card normally used in the 5D III. Power ON, switch to a supported shooting mode/LiveView, and try the standard Magic Lantern ERASE/menu shortcut once. Record whether the ML menu exists. Do not experiment with downloaded files or Canon's Firmware Update command.
3. **Public firmware check:** Verify the public Canon firmware number using a reliable, independent interface or qualified service; the camera's photographed Setup screen and original JPEG both showed only internal `9.0.1 A6(34)`. A model/MPU match is not enough to choose a firmware-update binary.
4. **Protect the source card:** Copy the Canon photo/video files safely to a PC first. If a known-working Magic Lantern card exists, preserve it, do not overwrite it, and use QVFilm v0.2.x read-only card backup/verify for its existing ML files. A copied folder does not replicate boot sectors or camera bootflags.
5. **Only then select a baseline build:** Review the original Magic Lantern `5D3.123` installation notes, original hashes, source provenance and supported boot steps. The first hardware trial must use a proven matching *baseline*, not QVFIL's custom MLV Lite. Avoid the experimental crop_rec/3K modules until stock Magic Lantern has been observed working.
6. **Exit and recovery plan:** Separate known-good media and a dedicated test card, charged battery, no conflicting devices, clear stop conditions (camera freeze, red write light, error, abnormal heat). If the camera fails to boot without the test card, stop; do not attempt speculative downgrade or bootflag edits.

### What may happen after those gates

- **If Canon firmware is independently confirmed 1.2.3, no ML card exists, and baseline installer has a verified safe compatibility path:** Review a **separate** install package and on-camera acceptance plan. This repository deliberately does not publish such a package yet.
- **If existing ML menu works but current inspected card has no ML files:** audit the card that actually boots ML; do not perform a first-time installation based on the wrong card.
- **If firmware cannot be independently confirmed or the body unexpectedly displays `9.0.1`:** stop and ask Canon support/an experienced 5D3 Magic Lantern maintainer to identify firmware without flashing.
- **If any metadata reports 1.3.x or a different camera model:** do not attempt a `5D3.123` install.

## Software development may continue in parallel

The `QVFIL` read-only dashboard and module were cross-compiled on Linux GitHub Actions (v0.1.0). That **does not establish** actual LCD layout, button handling, boot safety, 3K preset stability or recording performance. No QVFIL `.mo` will be offered as ready for installation until baseline camera commissioning and hardware tests succeed.

## Privacy and safety

Never upload original images, serial numbers, private memory-card contents or firmware dumps to a public issue. The public GitHub project should contain only code, documented synthetic tests and redacted results. No code may automatically set camera bootflags, overwrite original CF/SD cards, or silently upgrade/downgrade Canon firmware.
