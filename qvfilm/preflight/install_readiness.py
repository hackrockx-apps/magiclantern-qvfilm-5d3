#!/usr/bin/env python3
"""QVFilm v0.2.3: offline interpretation of v0.2.2 camera/card audit.
Never touches camera/media. Always treats missing independent hardware proof as HOLD.
"""
import argparse
import json
from pathlib import Path

VERSION = "0.2.3"


def assess(report):
    if not isinstance(report, dict):
        raise ValueError("Audit file must contain a JSON object.")
    card = report.get("card_status")
    if not isinstance(card, dict):
        card = {}
    camera_ok = report.get("camera_model_confirmed") is True
    mpu_candidate = report.get("public_firmware_candidate_from_community_mapping")
    card_status = str(card.get("status", "NOT_CHECKED"))
    has_boot = card.get("bootable_verified") is True
    blockers = []
    actions = []
    if not camera_ok:
        blockers.append("Camera model not independently identified as 5D Mark III.")
    if report.get("mapping_is_independent_firmware_proof") is not True:
        blockers.append("Canon public firmware version NOT independently verified.")
    # This program does not trust a single JSON boolean as independent proof
    # of boot safety, and is never an installation authorization.
    if card_status == "NO_ML_FILES":
        blockers.append("No Magic Lantern files found at the inspected card root.")
        actions.append("Confirm the inspected drive letter is the real camera card; NO_ML_FILES can also mean a stock Canon card.")
    elif card_status == "NOT_CHECKED":
        blockers.append("No inspected card data.")
        actions.append("Audit the correct CF/SD card with QVFilm v0.2.2.")
    elif card_status == "ML_FILES_SEEN_UNVERIFIED":
        blockers.append("Magic Lantern files present, but the card's actual bootability is unverified.")
        actions.append("Preserve any known-good card and confirm normal baseline operation on camera before testing QVFIL.")
    else:
        blockers.append("Card status requires physical review: " + card_status[:120])
    if not has_boot:
        blockers.append("No known-good Magic Lantern boot test has been recorded.")
    blockers.append("No reviewed camera-specific baseline installer and verified hardware recovery procedure.")
    actions.append("Keep original cards and Canon firmware unchanged; do not copy or flash QVFIL binaries.")
    actions.append("Have public Canon 1.2.3 version corroborated by a trusted independent source/technician.")
    return {
        "readiness_version": VERSION,
        "camera_target": "Canon EOS 5D Mark III / Magic Lantern 5D3.123",
        "camera_model_confirmed_in_photo": camera_ok,
        "internal_mpu_candidate": mpu_candidate,
        "mpu_is_not_public_firmware_proof": True,
        "inspected_card_status": card_status,
        "known_good_magic_lantern_card_boot_confirmed": has_boot,
        "decision": "DO_NOT_INSTALL",
        "blockers": blockers,
        "next_actions": actions,
        "caution": "This offline document does not inspect physical bootflags or validate a flashable installer."
    }


def main():
    p = argparse.ArgumentParser(description="Offline QVFilm readiness report; no camera/card writes.")
    p.add_argument("--audit", required=True, help="Path to qvfilm_compatibility_audit.json")
    p.add_argument("--out", required=True, help="Output JSON path on computer, never on the camera card")
    args = p.parse_args()
    src = Path(args.audit).expanduser().resolve()
    if not src.is_file():
        p.error("Audit JSON not found.")
    output = Path(args.out).expanduser().resolve()
    if src == output:
        p.error("Output cannot overwrite the source audit.")
    report = assess(json.loads(src.read_text(encoding="utf-8")))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("READINESS:", report["decision"], "|", report["inspected_card_status"])
    for item in report["blockers"]:
        print("- BLOCK:", item)
    print("Saved:", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
