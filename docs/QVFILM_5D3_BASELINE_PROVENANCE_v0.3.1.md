# QVFilm Magic Lantern — 5D3.123 baseline source provenance, v0.3.1

## Verified from user-provided files/screenshots

- Candidate camera: Canon EOS 5D Mark III.
- Prior camera internal MPU: `9.0.1 A6(34)`. ExifTool community mapping: corresponding *candidate* Canon public firmware `1.2.3`, **not independently verified on the user's body**.
- Both existing CF and SD cards have no `ML/` and no `autoexec.bin` according to the operator's inspection. There is no demonstrated known-good Magic Lantern boot card.
- Baseline source filename: `magiclantern.2025-06-20.5D3.123.zip`.
- Operator's `qvfilm_baseline_stage.json` reports 53 files, `ML-SETUP.FIR`, `autoexec.bin`, 51 `ML/` entries, CRC and layout checks passing.
- SHA-256 from that report **matches the SHA-256 visible in the operator's Magic Lantern download page screenshot**:

```text
63ca9e56405573ce58f9fca2680d17bb87ce57a5b946f66afc2cbb16ccf00d77
```

A screenshot checksum matching an operator-generated JSON is strong provenance evidence, but does not replace independent inspection of the original ZIP bytes or a signature verification. Do not infer the physical camera is definitely running firmware 1.2.3.

## New tools

- `qvfilm/preflight/source_audit.py --report "C:\path\qvfilm_baseline_stage.json"` creates a Windows/Linux PC-only provenance report `reports/qvfilm_source_audit.json`, marking checksum and structure consistency while keeping `DO_NOT_INSTALL`.
- Automated tests for correct/wrong hash, wrong platform, missing installer, and ensuring the install hold remains in place.

## One remaining hardware-compatibility gate: EOS Utility firmware display

Canon's EOS Utility manuals for EOS 5D Mark III explicitly document the **Firmware** item under the Camera Settings window, and say it can display the camera's firmware version. Relevant source:

https://gdlp01.c-wss.com/gds/2/0300014822/01/EOS_Utility_Win_Instruction_Manual_EN.pdf

**Safe read-only procedure (do NOT open updater):**

1. On Windows 10, install a supported Canon EOS Utility version obtained from Canon support for EOS 5D Mark III. Do not use third-party firmware-download sites.
2. With camera powered OFF, connect its supported USB cable to the computer; power ON. Close other image importers if they capture the device.
3. Launch EOS Utility, select `Camera settings/Remote shooting`, then `Camera settings`. Locate `Firmware` or `Firmware update` line and **read the displayed version only**.
4. **Do not click `Firmware update`**, `Next`, or any action that launches an update. Do not send `.FIR` over USB.
5. If EOS Utility explicitly displays `1.2.3`, record a screenshot (remove private identifiers) as independent supportive evidence. If it shows `9.0.1`, is unavailable, or reports a different value, keep `DO_NOT_INSTALL` and seek an experienced Canon/ML technician. Do not attempt firmware downgrade/upgrades to resolve uncertainty.

Important: EOS Utility reads the same physical camera and may use the same firmware-reported source; agreement is useful but not a cryptographic attestation. Physical hardware verification and safe recovery planning remain required.

## Following firmware confirmation

- Back up all photos from existing CF and SD cards.
- Preserve existing cards and use **a separate, blank, backed-up SD card** for the first baseline test.
- Review the exact baseline ML installer / card boot requirements, and secure a realistic stop/recovery plan.
- **Only after that**, perform the official-platform baseline installation with a fully charged battery and operator present. Never install QVFIL experimental module as the first Magic Lantern setup.
- Post-boot checks: Canon photo and H.264, menu, LiveView, power cycling, card state, no error or hangs.
- Only then evaluate the QVFIL overlay, followed by 3K RAW recording with dropped-frame and temperature monitoring.

**Status: SOURCE HASH MATCH / CAMERA FW UNVERIFIED / DO NOT INSTALL.**


## Superseding operator evidence — 2026-11-02

The original v0.3.1 provenance report predates camera commissioning. Its firmware and no-working-card statements are historical and superseded by these later operator results:

- The operator explicitly confirms public Canon firmware **1.2.3**. This matches the `5D3.123` baseline target.
- QVFIL v0.6.6 subsequently passed user hardware acceptance, proving the installed Magic Lantern environment boots and runs the accepted QVFIL build on this camera.
- A `ROM*.BIN` backup was reported PASS in the project checkpoint. This is not a full card image and does not establish a tested card recovery route.
- Keep the current v0.6.6 card untouched. A verified full-card clone/image and independent recovery check remain undocumented; hold any new experimental camera-module installation until that is complete.
- Do not upgrade Canon firmware to 1.3.3 or later. Canon states these versions cannot be downgraded to 1.2.3: https://www.cla.canon.com/en/support/product-advisories/adv-eos5d-markiii-miscpage

Updated state: `SOURCE_HASH_MATCH` / `CANON_FW_1_2_3_USER_CONFIRMED` / `ML_BOOT_V066_HARDWARE_PASS` / `ROM_BACKUP_PASS_REPORTED` / `FULL_CARD_RECOVERY_BACKUP_NOT_YET_VERIFIED` / `NEW_MODULE_INSTALL_HOLD`.
