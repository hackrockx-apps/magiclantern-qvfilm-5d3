# QVFilm 5D Mark III — Baseline staging v0.3.0 (Windows 10)

## Target

Canon EOS 5D Mark III; candidate firmware public version 1.2.3, based on internal MPU 9.0.1/A6 mapping.

**NO camera firmware installer is distributed by QVFilm v0.3.0.**
This phase ONLY validates a downloaded ZIP on a Windows PC. It neither
modifies the camera nor touches the boot flags, CF card or SD card.

## Why the staged process is necessary

The user confirmed BOTH CF and SD cards have no Magic Lantern directory:
no \`ML/\` and no \`autoexec.bin\`. Therefore there is currently no
demonstrated Magic Lantern boot card or verified restore route. The \`9.0.1 A6(34)\`
Canon menu / ExifTool evidence maps to a **candidate** 1.2.3 but not an
independent public firmware identity.

An earlier QVFilm \`mlv_lite.mo\` was cross-compiled for \`5D3.123\`, but
compilation alone is not evidence of safe camera installation.

## Download and inspect a *baseline* before any experimental fork

1. On the PC, download a baseline Magic Lantern build for **5D3.123 ONLY**
   from the Magic Lantern team's build portal:
   https://builds.magiclantern.fm/
2. If the portal is inaccessible, **do not substitute a random firmware ZIP**,
   the 5D3.113 build, or the 5D2.212 build. Ask for source validation of a
   specific alternate repository/release first.
3. Preserve the downloaded ZIP in a local PC folder. Do not unzip it onto SD or CF yet.
4. From this QVFilm v0.3.0 package, launch
   \`QVFILM_BASELINE_CHECK_WIN10.cmd\`.
5. Enter the **full local path** of the ZIP. Spaces in the path are supported.
6. The checker writes \`reports/qvfilm_baseline_stage.json\` on the PC.
   It checks SHA-256, naming, safe ZIP entry paths, CRC, \`autoexec.bin\`,
   \`ML/\` and a known \`5D3.123\` installer .FIR name.

### How to read its decision

- \`STRUCTURE_PASS_INSTALL_HOLD\`: ZIP layout looks plausible and was
  internally readable. **This is NOT a safe-to-install approval.**
- \`REVIEW_NAME\`: Missing explicit 5D3.123 target in filename;
  investigate release provenance.
- \`BLOCK\`: Wrong model/firmware, incomplete files or unsafe/corrupt archive.
  Do NOT use that ZIP.

The checker cannot independently authenticate the publisher or firmware.
An attacker could create a ZIP that passes every structural check.
Use the upstream source, not file layout alone, for authenticity.

## Hardware prerequisites before first installation

- A separate small SD/SDHC test card (preferably ≤32GB, with all contents
  backed up). **Keep the existing SD and CF cards untouched.**
- Verify Canon's *public* firmware version is in fact 1.2.3 with a trusted
  independent source / camera technician, not just MPU 9.0.1/A6.
- A fully charged and healthy Canon LP-E6 battery.
- Camera body operates normally with its stock Canon menus and recording.
- A reviewed matching 5D3.123 baseline setup package and complete installer
  notes; a hardware-tested rollback path for that version.
- Understand that on-camera firmware update for Magic Lantern
  changes a persistent **boot flag**, even when Canon ROM is not replaced.
  Removing the card will not undo every possible boot issue.
- Never run an update if a file does not clearly belong to the right camera,
  platform and known build, or if power is unstable.

## After a baseline is approved (future phase)

The Magic Lantern team's generic install procedure typically formats a
**dedicated, backed-up** card in-camera, puts baseline files at the card root,
and triggers the on-camera Firmware Update from the Canon Setup menu.
The first-install code changes boot state. This project does NOT automate
that action or tell the user to execute it before source+firmware verification.

Follow-up hardware tests: stock Canon still works; boot, LCD, menu, LiveView,
battery, CF/SD, full power-cycle/recovery; THEN minimal RAW; THEN QVFIL UI;
3K RAW recording is the final test.

## Current live code and results

- Fork: https://github.com/hackrockx-apps/magiclantern-qvfilm-5d3
- v0.1.0 QVFIL module: compiled (no camera test).
- v0.2.2: metadata review identified MPU 9.0.1 A6, with install hold.
- v0.2.3: card audit result NO_ML_FILES; compatibility unresolved.
- v0.3.0: offline baseline ZIP staging and checksum report (no install).

## References

- Community Magic Lantern installation and boot flag cautions:
  https://magiclantern.fandom.com/wiki/Unified/Install
- Canon official manual (formatting deletes existing photos):
  https://asia.canon/en/support/8201359000
- Community mapping of firmware 1.2.3 ↔ MPU 9.0.1/A6:
  https://github.com/exiftool/exiftool/issues/399
