#!/usr/bin/env python3
"""QVFilm v0.2.2: read-only review of preflight JSON and card inventory.
No firmware files, installer, camera connection, or write to removable media.
SPDX-License-Identifier: GPL-2.0-or-later
"""
import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

TARGET = "5D3.123"
SOURCE_URL = "https://github.com/exiftool/exiftool/issues/399"


def sha256(file):
    h = hashlib.sha256()
    with file.open("rb") as f:
        for buf in iter(lambda: f.read(1024 * 1024), b""):
            h.update(buf)
    return h.hexdigest()


def recognized_mpu(metadata):
    # Community-sourced examples. These are NOT a firmware authenticity check.
    vals = " ".join(str(v) for k, v in metadata.items()
                    if k.split(":")[-1] in ("CanonFirmwareVersion",
                                               "FirmwareVersion", "FirmwareInfo"))
    if re.search(r"(?<!\d)9\.0\.1(?!\d)", vals) and re.search(r"\bA6\b", vals):
        return ("1.2.3", "MPU 9.0.1 / A6")
    if re.search(r"(?<!\d)9\.3\.9(?!\d)", vals) and re.search(r"\bAB\b", vals):
        return ("1.3.6", "MPU 9.3.9 / AB")
    return (None, None)


def card_inventory(card_path):
    """Inventory known ML filenames from a provided card root without changing it."""
    card = Path(card_path).expanduser().resolve()
    if not card.is_dir():
        return {"status": "CARD_UNAVAILABLE", "reason": "Card root not accessible."}
    targets = ("autoexec.bin", "ML-SETUP.FIR")
    files = {}
    for name in targets:
        p = card / name
        if p.is_symlink():
            return {"status": "UNSAFE_PATH", "reason": "Symlink in card root."}
        if p.is_file():
            files[name] = {"bytes": p.stat().st_size, "sha256": sha256(p)}
    ml = card / "ML"
    if ml.is_symlink():
        return {"status": "UNSAFE_PATH", "reason": "ML folder is a symlink."}
    modules = []
    if ml.is_dir():
        # Different builds use uppercase or lowercase modules directory.
        mod_dirs = [p for p in ml.iterdir() if p.name.lower() == "modules"
                    and p.is_dir() and not p.is_symlink()]
        for d in mod_dirs:
            for p in sorted(d.iterdir(), key=lambda f: f.name.lower()):
                if p.is_symlink():
                    continue
                if p.is_file() and p.suffix.lower() == ".mo":
                    modules.append(p.name)  # names only; do not read settings or photos
    return {
        "status": "ML_FILES_SEEN_UNVERIFIED" if files or ml.is_dir() else "NO_ML_FILES",
        "bootable_verified": False,
        "file_fingerprints": files,
        "ml_directory_present": ml.is_dir(),
        "module_names": sorted(set(modules))[:100],
        "note": "Directory and hashes do NOT prove bootability or compatibility.",
    }


def review(report, card=None):
    if not isinstance(report, dict):
        raise ValueError("Report must be a JSON object.")
    meta = report.get("camera_metadata") or {}
    if not isinstance(meta, dict):
        meta = {}
    model = str(next((v for k, v in meta.items() if k.split(":")[-1] == "Model"), ""))
    prior = str(report.get("status") or "")
    mpu_fw, mpu_label = recognized_mpu(meta)
    model_ok = "5D Mark III" in model
    data_ok = prior in {"REVIEW_REQUIRED", "PASS_METADATA", "BLOCK_MISMATCH"}
    candidate = mpu_fw if model_ok and data_ok else None
    result = {
        "audit_version": "0.2.2",
        "utc": datetime.now(timezone.utc).isoformat(),
        "camera_platform_target": TARGET,
        "photo_name": str(report.get("photo_name", ""))[:160],
        "photo_sha256": str(report.get("photo_sha256", ""))[:100],
        "source_preflight_status": prior,
        "camera_model_confirmed": model_ok,
        "mpu_evidence": mpu_label if model_ok else None,
        "public_firmware_candidate_from_community_mapping": candidate,
        "mapping_source": SOURCE_URL,
        "mapping_is_independent_firmware_proof": False,
        "installation_decision": "HOLD_NOT_APPROVED",
        "card_status": {"status": "NOT_CHECKED", "reason": "No card path given."},
        "next_checks": [
            "Verify public Canon firmware version independently; MPU alone is insufficient.",
            "Read-only audit the actual SD/CF card used by the camera.",
            "Preserve a known-good ML boot card and verified computer backup if one exists.",
            "Do not copy .FIR, autoexec.bin or QVFIL .mo to the camera card.",
        ],
        "limitations": [
            "The program cannot communicate with the camera or validate boot flags.",
            "No RAW 3K, LCD or camera-button testing has been performed.",
        ],
    }
    if card:
        result["card_status"] = card_inventory(card)
    if not model_ok or prior == "BLOCK_MISMATCH":
        result["public_firmware_candidate_from_community_mapping"] = None
        result["next_checks"][0] = "Body/firmware mismatch: stop and verify the correct camera."
    return result


def main():
    p = argparse.ArgumentParser(
        description="Read-only Canon 5D3 compatibility review; never installs firmware.")
    p.add_argument("--report", required=True, help="qvfilm_preflight_report.json")
    p.add_argument("--card", default="", help="Optional card root, e.g. G:\\")
    p.add_argument("--out", default="reports", help="OUTPUT folder on computer, not card")
    args = p.parse_args()

    source = Path(args.report).expanduser().resolve()
    if not source.is_file():
        p.error("Preflight report does not exist.")
    card = Path(args.card).expanduser().resolve() if args.card else None
    out = Path(args.out).expanduser().resolve()
    if card is not None and (card == out or card in out.parents):
        p.error("Output directory must not be located on the camera card.")
    if card is not None and out == card.parent:
        p.error("Output directory must not be the card's parent directory.")
    data = json.loads(source.read_text(encoding="utf-8"))
    result = review(data, args.card)
    out.mkdir(parents=True, exist_ok=True)
    dest = out / "qvfilm_compatibility_audit.json"
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("QVFILM AUDIT:", result["installation_decision"])
    print("Camera model:", "CONFIRMED" if result["camera_model_confirmed"] else "NOT CONFIRMED")
    print("MPU-based candidate (NOT VERIFIED):",
          result["public_firmware_candidate_from_community_mapping"] or "none")
    print("Card:", result["card_status"]["status"])
    print("Report:", str(dest))
    print("NO CAMERA OR CARD WRITES. DO NOT INSTALL QVFIL.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
