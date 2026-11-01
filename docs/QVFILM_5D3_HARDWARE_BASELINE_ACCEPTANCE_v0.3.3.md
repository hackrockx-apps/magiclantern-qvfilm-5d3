# QVFilm EOS 5D Mark III — Hardware baseline acceptance v0.3.3

**Evidence date:** 2026-11-01  
**Camera:** Canon EOS 5D Mark III  
**Magic Lantern build shown on LCD:** \`2025-06-20.5D3.123\`  
**Current status:** INSTALLER DONE / MAGIC LANTERN BOOT & MENU PASS; RECORDING/RAW NOT YET VERIFIED.

## User-supplied photo evidence

1. Canon Setup screen shows \`Firmware Ver.: 9.0.1 A6(34)\` (internal MPU; do not label it Canon public firmware 9.0.1).
2. Magic Lantern installer LCD states \`Backing up ROM0...\`, \`Backing up ROM1...\`, \`Boot flag is already set.\`, \`Making card bootable...\`, \`Done!\`, and \`Please restart your camera.\`
3. After reboot the Magic Lantern development warning appears and identifies \`Magic Lantern version: 2025-06-20.5D3.123\`, commit \`ed3e7c0df\` (as rendered on the photo).
4. Magic Lantern Help screen is visible, with navigation instructions and the same version in the footer.

**Important interpretation:** \`Boot flag is already set\` is not an installer failure. It implies persistent bootflag was already set by the time the installer checked; this does not prove if/when Magic Lantern had previously been installed. No claim is made that the camera is 100% stable or fully recoverable.

## Immediate Stage A — protect ROM and card contents

**Do this before enabling RAW, modules or QVFIL UI.**

1. Power off normally. Once card LED is inactive, remove the dedicated SD test card and connect to Windows via reader.
2. Check \`<SD>:\ML\LOGS\` for \`ROM*.BIN\` (commonly \`ROM0.BIN\` and \`ROM1.BIN\`). **Do not delete or rename files.**
3. Copy ROM files to private PC directory, e.g. \`Z:\5D Mark III Upgrade\BACKUP_ROM\`. Do not commit these to public GitHub, upload to untrusted cloud or share in chat.
4. For additional integrity check, run existing \`qvfilm/preflight/preflight.py backup --card <SD> --dest <new PC folder>\` on the exact known-boot SD card; the tool compares source/copy SHA-256 and includes \`ML/\`, including its LOGS directory; run \`verify-backup\` on the output. The backup verifies file copies, **not boot sectors or a functional firmware recovery pathway**.
5. Preserve original SD test card and the pristine baseline ZIP + its known SHA-256. Avoid overlaying experimental files onto the baseline card.

## Stage B — stock-camera smoke tests

Reinsert same SD test card; keep custom QVFIL \`.mo\` OUT.

| Test | Action | Acceptance criterion |
|---|---|---|
| B1 Boot / restart | Power OFF, then ON twice with test SD inserted | Canon starts without error, Magic Lantern splash/menu loads |
| B2 ML navigation | Press ERASE; navigate with top dial and joystick/rear dial; use INFO help and Q/PLAY submenu | Menu works, camera controls still responsive |
| B3 Still photograph | Exit ML menu, capture one regular JPG or CR2 | File saved normally, playback works |
| B4 LiveView | Toggle LiveView, briefly inspect preview | Frame updates without crash/major corruption |
| B5 Standard H.264 | Record 10-20 seconds at Canon 1080p 24/25/30 fps | File plays with expected audio/video |
| B6 Temperature/power | After simple tests, power off normally | No lockup, abnormal heat or card write LED hung |

Do not activate RAW recording at Stage B. A single failure stops progression; record error text and restore the known working media.

## Stage C — RAW recording gate (only after B1–B6 pass)

1. Inspect \`Modules\` tab and identify which stock MLV recording modules exist in the *2025 development build*. Module names differ across builds: do not assume \`mlv_lite\`, \`mlv_rec\` or \`raw_rec\` must all appear.
2. Enable only the supported MLV RAW recorder and restart as the menu instructs.
3. Use the \`Movie\` tab to identify a conservative 1080p 23.976/25 RAW setting; enable only after checking card sustained write speed and recorder status.
4. Record 5–10 s test shot, stop normally, verify file on PC and inspect dropped frames before attempting a longer clip.
5. Do **not** enable 3K/crop_rec yet. The QVFIL experimental \`mlv_lite.mo\` was cross-compiled but has not been accepted on real LCD. Never replace the stock module on the original boot SD.

## Operational controls shown on the user's Help screenshot

- \`ERASE\` (trash): open/close Magic Lantern menu.
- \`INFO\`: show context help.
- \`Q / PLAY\`: open submenu.
- \`SET\` and dials: edit values / navigate (as contextual help displays).

## Reporting and next gate

After Stage A/B report: ROM files located and backed up (YES/NO), full SD backup verified (YES/NO), boot/restart PASS/FAIL, Magic Lantern menu PASS/FAIL, Canon stills PASS/FAIL, LiveView PASS/FAIL, H.264 recording PASS/FAIL and any error message. Provide a photo of the module list only if these baseline tests pass. Keep ROM dumps/private backup OFF public issues.

**Engineering caution:** Successful install and boot do not by themselves prove 3K continuous capture, CF write speed, or that the custom UI is safe. Firmware or bootflag state must not be altered to bypass test failures.
