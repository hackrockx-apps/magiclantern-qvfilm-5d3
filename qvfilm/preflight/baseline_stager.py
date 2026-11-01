#!/usr/bin/env python3
"""QVFilm baseline Magic Lantern ZIP staging: READ ONLY. No SD/CF or camera writes.

Checks filename, archive paths, payload structure, CRC and SHA-256 to catch
obvious errors; DOES NOT authenticate the release or authorize installation.
SPDX-License-Identifier: GPL-2.0-or-later
"""
import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

TARGET = "5D3.123"
VERSION = "0.3.0"
MAX_ENTRIES = 1200
MAX_UNCOMPRESSED = 128 * 1024 * 1024
MAX_COMPRESSED = 64 * 1024 * 1024
REQUIRED = {"autoexec.bin"}
KNOWN_SETUP_FIRS = {"ML-SETUP.FIR", "ML-5D3-123.FIR", "ML5D3123.FIR"}
FIRMWARE_BINS = {".FIR", ".BIN"}
FORBIDDEN = {".EXE", ".BAT", ".CMD", ".PS1", ".VBS", ".SCR"}


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_name(name):
    return name.replace("\\", "/")


def analyze_archive(path):
    path = Path(path).expanduser().resolve()
    result = {
        "version": VERSION,
        "target": TARGET,
        "source_filename": path.name,
        "source_sha256": None,
        "archive_readable": False,
        "structure": {},
        "decision": "BLOCK",
        "reason": "",
        "warnings": [
            "Archive name and contents are NOT proof of official provenance.",
            "Do not install Magic Lantern until Canon public firmware is independently verified and the camera-specific installer is reviewed.",
            "This program does not write to camera or memory card.",
        ],
    }
    if not path.is_file() or path.suffix.lower() != ".zip":
        result["reason"] = "Please select a local .zip release archive on the PC."
        return result
    result["source_sha256"] = digest(path)
    if re.search(r"(?i)(5D2|5D4|5D3[._-]113|5D3[._-]133|5D3[._-]136)", path.name):
        result["reason"] = "ZIP filename appears to target a different Canon body or firmware."
        return result
    if not re.search(r"(?i)5D3[._-]?123", path.name):
        result["reason"] = "ZIP filename does not positively identify 5D3.123. Manual provenance review required."
        result["decision"] = "REVIEW_NAME"
        return result
    if path.stat().st_size > MAX_COMPRESSED:
        result["reason"] = "Archive too large for a baseline release; inspect manually."
        return result
    try:
        with zipfile.ZipFile(path) as z:
            entries = z.infolist()
            if len(entries) > MAX_ENTRIES:
                result["reason"] = "Too many archive entries."
                return result
            if sum(f.file_size for f in entries) > MAX_UNCOMPRESSED:
                result["reason"] = "Archive expands beyond safe inspection limit."
                return result
            files = []
            normalized = set()
            for info in entries:
                name = normalize_name(info.filename)
                # Reject path traversal, Windows drive paths, ambiguous separators,
                # duplicate case-insensitive names, symlinks and excessive expansion.
                components = name.split("/")
                if (not name or name[0] == "/" or re.match(r"^[A-Za-z]:", name)
                        or any(c in ("", ".", "..") for c in components if c != components[-1])
                        or ".." in components or ":" in name or name.startswith("//")):
                    result["reason"] = "Unsafe archive path detected."
                    return result
                if info.external_attr >> 16 & 0o170000 == 0o120000:
                    result["reason"] = "Symlink in archive is not accepted."
                    return result
                if not info.is_dir():
                    if name.casefold() in normalized:
                        result["reason"] = "Duplicate case-insensitive archive entry."
                        return result
                    normalized.add(name.casefold())
                    if info.file_size and info.compress_size and info.file_size / info.compress_size > 1000:
                        result["reason"] = "Extreme compression ratio."
                        return result
                    if Path(name).suffix.upper() in FORBIDDEN:
                        result["reason"] = "Unexpected executable/script file in camera installation ZIP."
                        return result
                    files.append(name)
            if z.testzip() is not None:
                result["reason"] = "Corrupt ZIP member (CRC failure)."
                return result
            upper = {f.upper(): f for f in files}
            ml_files = [f for f in files if f.upper().startswith("ML/")]
            root_missing = [r for r in REQUIRED if r.upper() not in upper]
            setup_files = [f for f in files if f.upper() in KNOWN_SETUP_FIRS]
            if not setup_files:
                root_missing.append("5D3.123 matching installer .FIR")
            unknown_firmware = [f for f in files
                                if Path(f).suffix.upper() in FIRMWARE_BINS
                                and f.upper() not in (KNOWN_SETUP_FIRS | {"AUTOEXEC.BIN"})
                                and not f.upper().startswith("ML/")]
            result["archive_readable"] = True
            result["structure"] = {
                "file_count": len(files),
                "total_uncompressed_bytes": sum(f.file_size for f in entries),
                "autoexec_present": "AUTOEXEC.BIN" in upper,
                "setup_fir_present": bool(setup_files),
                "setup_fir_names": setup_files,
                "ml_file_count": len(ml_files),
                "missing_required": sorted(root_missing),
                "unexpected_root_firmware_bins": unknown_firmware,
            }
            if root_missing or not ml_files or unknown_firmware:
                result["reason"] = "Required root files or ML payload missing, or unexpected firmware binaries present."
                return result
            result["decision"] = "STRUCTURE_PASS_INSTALL_HOLD"
            result["reason"] = "5D3.123 naming, required files, archive paths and CRC passed; physical compatibility still unverified."
            return result
    except (zipfile.BadZipFile, RuntimeError, EOFError, OSError, ValueError) as e:
        result["reason"] = "Cannot safely read ZIP: " + str(e)[:200]
        return result


def stage(zip_path, out_path):
    original = Path(zip_path).expanduser().resolve()
    target = Path(out_path).expanduser().resolve()
    if target == original:
        raise ValueError("Report path cannot replace source ZIP.")
    info = analyze_archive(original)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(info, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("QVFilm baseline staging:", info["decision"])
    print(info["reason"])
    print("Report:", target)
    print("CAMERA MEDIA WAS NOT MODIFIED. DO NOT INSTALL DIRECTLY FROM THIS REPORT.")
    return 0 if info["decision"] == "STRUCTURE_PASS_INSTALL_HOLD" else 2


def main():
    p = argparse.ArgumentParser(description="QVFilm camera-baseline ZIP inspection (PC only)")
    p.add_argument("--zip")
    p.add_argument("--out")
    args = p.parse_args()
    here = Path(__file__).resolve().parent
    if args.zip:
        selected = args.zip.strip().strip('"')
    else:
        print("Select a LOCAL baseline ZIP, preferably from https://builds.magiclantern.fm/")
        selected = input("Path to downloaded 5D3.123 ZIP on PC: ").strip().strip('"')
    if not selected:
        print("No ZIP selected. Nothing modified.")
        return 2
    dest = args.out or str(here / "reports" / "qvfilm_baseline_stage.json")
    try:
        return stage(selected, dest)
    except (OSError, ValueError) as exc:
        print("BLOCKED:", exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
