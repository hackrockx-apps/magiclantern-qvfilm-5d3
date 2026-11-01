# QVFilm 5D3.123 — SAFE PREFLIGHT / RECOVERY v0.2.0

**Windows 10, read-only camera-card workflow. NO camera-installation files are included.**

Target: **Canon EOS 5D Mark III**; expected Canon firmware **1.2.3**; Magic Lantern build target \`5D3.123\`.

## DO NOT INSTALL YET

This package is **NOT** an installation or a downgrade utility. It contains no \`.FIR\`, \`autoexec.bin\` or customized \`.mo\`. It does not unlock 3K modes and does not write to the camera or a CF/SD card. An offline metadata pass cannot guarantee that a firmware patch or boot card is safe.

The current photographed Canon Setup menu says \`9.0.1 A6(34)\`. That is believed to describe the internal MPU firmware, **not** Canon's public firmware version number. ExifTool issue #399 records the pair Canon **1.2.3 ↔ MPU 9.0.1 / A6** for 5D Mark III, but internal MPU matching **alone** is NOT an installation approval.

References:
- https://github.com/exiftool/exiftool/issues/399
- https://exiftool.org/TagNames/Canon.html
- https://github.com/hackrockx-apps/magiclantern-qvfilm-5d3

## 1. Required preparation

1. Use Windows 10 with Python 3 installed.
2. Download **ExifTool for Windows from the official source**: https://exiftool.org/ . Rename the downloaded executable to \`exiftool.exe\` if necessary and place it in the package's \`tools\` folder. Alternatively, add it to your Windows PATH. **We do not distribute ExifTool binaries.**
3. On the 5D Mark III, **shoot a NEW original JPEG or CR2** and copy it to the PC without resizing, editing, stripping metadata or taking a screenshot. The previous photo showing the Canon screen is useful context, but cannot substitute for an original in-camera photo.
4. If Magic Lantern currently boots from a known-good card, **keep that card untouched**. A second card is only used later, after a separate installation plan has passed review.
5. Create a backup destination on the computer, **not on the card** (e.g. \`C:\QVFilm\5D3\ML_backup_20261101\`). Its final folder **must not already exist**.

## 2. Run on Windows

Double-click \`QVFILM_START_WIN10.cmd\` inside this folder.

- **1 — Scan original photo**: Enter full path to original JPG/CR2, optionally the CF/SD card drive. Writes only \`reports/qvfilm_preflight_report.json\` beside the Windows launcher. It does NOT write to the card.
- **2 — Backup a known-good ML card**: Copy only \`autoexec.bin\`, \`ML/\` and \`ML-SETUP.FIR\` if present, to a **new** PC folder. File-by-file SHA-256 is compared against the source. DCIM/photographs/footage are deliberately excluded: back up valuable footage separately.
- **3 — Verify copied backup**: Compare all files against \`BACKUP_MANIFEST.json\`. A \`BACKUP_COMPLETE.txt\` marker is written ONLY after all original/copy SHA-256 checks pass.

All operations are designed to be one-way: **camera card → computer**. No formatting, bootflag changes, firmware writes, card restore writes or Canon firmware updates are performed. A verified directory backup is NOT automatically a bootable recovery card.

Advanced command line:

\`\`\`powershell
py -3 preflight.py scan --photo "C:\Photos\IMG_0001.CR2" --card "E:\" --out "reports"
py -3 preflight.py backup --card "E:\" --dest "C:\QVFilm\5D3\ml_known_good_20261101"
py -3 preflight.py verify-backup --dir "C:\QVFilm\5D3\ml_known_good_20261101"
\`\`\`

## 3. Interpret compatibility result

| Status | Meaning | May install QVFIL firmware? |
|---|---|---|
| \`PASS_METADATA\` | Original image metadata identifies **5D Mark III** and explicit public firmware **1.2.3**. | **NO**. Continue safety and bootability checks first. |
| \`REVIEW_REQUIRED\` | Camera/Canon version missing, or only MPU \`9.0.1 A6(34)\` identified; ExifTool missing also gives review. | **NO** |
| \`BLOCK_MISMATCH\` | Wrong body, public version other than 1.2.3, or conflicting tags. | **NO** |

For a later camera installation decision (outside this package), require ALL of:
- Source hardware and firmware independently verified as 5D3 + 1.2.3, including inspection of camera firmware/version evidence;
- A known-good boot card preserved and checksummed (if one exists);
- A matching baseline Magic Lantern build successfully tested independently;
- A **complete camera-specific boot/installer package**, reviewed by a maintainer;
- Battery/CF/SD verified; tested power-loss and uninstall procedure available for the specific build;
- QVFIL module hardware test, LiveView/record button validation, thermal and 3K frame-drop/recording test.
- No unexpected warnings or crashes.

## 4. Recovery precautions

**Before installing anything in a future phase:** preserve a known-good original card, a PC backup and a second blank test card. Keep all sources and hashes. Do **not** overwrite the original card. Never install a QVFIL prototype \`.mo\` onto a working card just because it compiles.

**If the camera appears frozen after inserting a test card:** stop, turn it OFF, wait for card LED activity to stop, and remove the test card. With camera OFF, remove/reseat the battery if necessary; try powering ON with no card, and only then try the known-good card if the body behaves normally. Do not repeatedly reboot or initiate a speculative downgrade. If the camera still fails without the test card, **stop and consult qualified Canon service / an experienced Magic Lantern developer**. Bootflag corruption cannot be guaranteed recoverable by removing the card.

**If RAW capture fails / dropped frames:** stop tests, preserve the source MLV files, revert to the known-good card, and do not shoot non-repeatable work with experimental firmware.

This package intentionally cannot restore a card to bootable status by itself: automatic card writing would increase risk. After hardware verification, restoring ML boot media must use the **specific known-good procedure and boot flags for that body**, not a generic copy operation.

## 5. Privacy and integrity

The preflight report contains the selected picture's filename, SHA-256, camera model and public firmware tag values only. Serial numbers, owner names and GPS data are not exported. The original photo is not modified or uploaded. Only the user can choose to share the report; do not commit raw photos or private reports to a public GitHub repository.

Run the synthetic unit tests locally with:

\`\`\`powershell
py -3 -m unittest discover -s . -p "test_preflight.py" -v
\`\`\`

## 6. Current engineering state

- Base branch \`qvfilm/v0.1.0-ui-prototype\` has successfully compiled \`platform/5D3.123\` and \`mlv_lite.mo\` in GitHub Actions, but has **not** passed testing on real hardware.
- Branch \`qvfilm/v0.2.0-preflight-recovery\` adds this cautious offline safety gate. It intentionally does not provide a flashable or installable firmware bundle.
- Release status: **OFFLINE QA ONLY / NOT FOR INSTALLATION**.
