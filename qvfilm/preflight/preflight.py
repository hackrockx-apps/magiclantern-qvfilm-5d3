#!/usr/bin/env python3
# QVFilm 5D3 preflight and recovery backup tool.
# Offline-first; reads only from camera cards; NEVER writes to the card.
# SPDX-License-Identifier: GPL-2.0-or-later
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

TARGET_CAMERA = "EOS 5D Mark III"
TARGET_FIRMWARE = "1.2.3"
TARGET_PLATFORM = "5D3.123"
COPY_ROOTS = ("autoexec.bin", "ML", "ML-SETUP.FIR")
REPORT_VERSION = "0.2.2"
FW_PATTERN = re.compile(r"(?<!\d)(1\.\d+\.\d+)(?!\d)")


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def is_inside(candidate, parent):
    return candidate == parent or parent in candidate.parents


def classify_metadata(metadata):
    """Pure classifier. An MPU string alone is NEVER a firmware-version pass."""
    models = [str(value).strip() for key, value in metadata.items()
              if key.split(":")[-1] in ("Model", "CameraModelName") and value is not None]
    if not models:
        return ("REVIEW_REQUIRED", "Camera model tag missing.")
    if any("5D Mark III" not in v for v in models):
        return ("BLOCK_MISMATCH", "Camera model does not consistently identify Canon EOS 5D Mark III.")
    candidates = []
    for key, value in metadata.items():
        if key.split(":")[-1] in ("CanonFirmwareVersion", "FirmwareVersion") and value is not None:
            # Do not treat internal MPU 9.0.1 as a Canon 1.x firmware revision.
            candidates.extend(FW_PATTERN.findall(str(value)))
    unique = sorted(set(candidates))
    if any(v != TARGET_FIRMWARE for v in unique):
        return ("BLOCK_MISMATCH", "Firmware metadata conflicts with required 1.2.3: " + ", ".join(unique))
    if unique == [TARGET_FIRMWARE]:
        return ("PASS_METADATA", "5D Mark III and Canon firmware 1.2.3 identified in the original photo metadata.")
    return ("REVIEW_REQUIRED",
            "No definitive Canon firmware 1.2.3 tag. Internal MPU 9.0.1/A6 is only supporting evidence.")

def find_exiftool():
    folder = Path(__file__).resolve().parent
    for candidate in (folder / "tools" / "exiftool.exe",
                      folder / "exiftool.exe"):
        if candidate.is_file():
            return str(candidate)
    for name in ("exiftool", "exiftool.exe"):
        hit = shutil.which(name)
        if hit:
            return hit
    return None


def collect_metadata(photo):
    exe = find_exiftool()
    if not exe:
        raise RuntimeError(
            "ExifTool missing. Put exiftool.exe AND the exiftool_files folder "
            "from the official Windows ZIP (https://exiftool.org/) into "
            "the tools folder beside preflight.py, or add ExifTool to PATH. "
            "Rename exiftool(-k).exe to exiftool.exe. No firmware decision was made.")
    cmd = [exe, "-j", "-G1", "-s", "-a",
           "-Model", "-CameraModelName",
           "-CanonFirmwareVersion", "-FirmwareVersion", "-FirmwareInfo",
           str(photo)]
    p = subprocess.run(cmd, text=True, capture_output=True, timeout=45,
                       encoding="utf-8", errors="replace", check=False)
    if p.returncode != 0:
        raise RuntimeError("ExifTool failed; inspect the original photo (exit %s): %s" %
                           (p.returncode, p.stderr.strip()[:240]))
    obj = json.loads(p.stdout)
    if len(obj) != 1 or not isinstance(obj[0], dict):
        raise RuntimeError("ExifTool did not return one readable metadata record.")
    return obj[0], exe


def sanitized_fields(metadata):
    allowed = {"Model", "CameraModelName", "CanonFirmwareVersion",
               "FirmwareVersion", "FirmwareInfo"}
    return {k: str(v)[:160] for k, v in metadata.items()
            if k.split(":")[-1] in allowed}


def scan(args):
    photo = Path(args.photo).expanduser().resolve()
    if not photo.is_file() or photo.suffix.lower() not in {".jpg", ".jpeg", ".cr2"}:
        raise ValueError("Use an ORIGINAL JPG/JPEG/CR2 produced by this 5D Mark III (not a screenshot).")
    result = {
        "report_version": REPORT_VERSION, "camera_platform": TARGET_PLATFORM,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "photo_name": photo.name, "photo_sha256": sha256(photo),
        "status": "REVIEW_REQUIRED", "camera_metadata": {},
        "warning": "Never install or downgrade firmware based on this report alone."
    }
    try:
        metadata, _ = collect_metadata(photo)
        status, reason = classify_metadata(metadata)
        result.update({"status": status, "reason": reason,
                       "camera_metadata": sanitized_fields(metadata)})
    except (RuntimeError, ValueError, json.JSONDecodeError, subprocess.TimeoutExpired) as e:
        result["reason"] = str(e)
    if args.card:
        card = Path(args.card).expanduser().resolve()
        if not card.is_dir():
            result["card"] = {"status": "ERROR", "reason": "Card directory not accessible."}
        else:
            present = [x for x in COPY_ROOTS if (card / x).exists()]
            result["card"] = {"status": "PRESENT" if present else "NO_ML_FILES",
                              "ml_roots_found": present,
                              "note": "Presence is not proof of a compatible boot card."}
    outdir = Path(args.out).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    reportfile = outdir / "qvfilm_preflight_report.json"
    reportfile.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")
    print("\nQVFilm PREFLIGHT: " + result["status"])
    print(result["reason"])
    print("Report: " + str(reportfile))
    print("NO FILES WRITTEN TO CAMERA CARD.")
    return 0 if result["status"] == "PASS_METADATA" else 2


def safe_file_tree(card):
    for root in COPY_ROOTS:
        source = card / root
        if source.is_symlink():
            raise ValueError("Symlink/junction in card root: " + root)
        if source.is_file():
            yield source, Path(root)
        elif source.is_dir():
            for base, dirs, names in os.walk(source, followlinks=False):
                basepath = Path(base)
                for d in dirs:
                    if (basepath / d).is_symlink():
                        raise ValueError("Symlink/junction under ML directory.")
                for name in sorted(names):
                    f = basepath / name
                    if f.is_symlink():
                        raise ValueError("Symlink/junction under ML directory.")
                    if f.is_file():
                        yield f, f.relative_to(card)


def backup(args):
    card = Path(args.card).expanduser().resolve()
    dest = Path(args.dest).expanduser().resolve()
    if not card.is_dir():
        raise ValueError("Card path is not an accessible folder / drive root.")
    if is_inside(dest, card) or is_inside(card, dest):
        raise ValueError("Backup destination must be separate from the card and must not contain it.")
    if dest.exists():
        raise ValueError("Backup folder already exists. Use a NEW empty backup destination.")
    files = sorted(list(safe_file_tree(card)), key=lambda p: str(p[1]).lower())
    if not files:
        raise ValueError("No Magic Lantern files found to back up. Nothing copied.")
    if args.max_gb > 0:
        bytes_to_copy = sum(p.stat().st_size for p, _ in files)
        if bytes_to_copy > args.max_gb * 1024**3:
            raise ValueError("Backup size exceeds --max-gb safeguard; inspect card first.")
    dest.mkdir(parents=True, exist_ok=False)
    (dest / "INCOMPLETE.txt").write_text(
        "Backup started. Do not trust until BACKUP_COMPLETE.txt exists.\n", encoding="utf-8")
    manifest = []
    try:
        for source, rel in files:
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            source_hash = sha256(source)
            copied_hash = sha256(target)
            if source_hash != copied_hash:
                raise IOError("Hash mismatch while copying " + rel.as_posix())
            manifest.append({"path": rel.as_posix(), "size": target.stat().st_size,
                             "sha256": copied_hash})
        (dest / "BACKUP_MANIFEST.json").write_text(
            json.dumps({"tool": "QVFilm Recovery", "version": REPORT_VERSION,
                        "camera_target": TARGET_PLATFORM, "files": manifest},
                       indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (dest / "BACKUP_COMPLETE.txt").write_text(
            "Read-only backup verified with SHA-256. This is NOT a verified bootable recovery card.\n",
            encoding="utf-8")
        (dest / "INCOMPLETE.txt").unlink()
        print("PASS_BACKUP: %d files, each source/copy SHA-256 matched." % len(manifest))
        print("Folder: " + str(dest))
        print("Camera card was read-only. Do not overwrite the known-good card.")
        return 0
    except Exception:
        print("INCOMPLETE backup left for inspection; not approved for recovery.", file=sys.stderr)
        raise


def verify_backup(args):
    backup_dir = Path(args.dir).expanduser().resolve()
    if not (backup_dir / "BACKUP_COMPLETE.txt").is_file():
        raise ValueError("Backup completion marker missing.")
    manifest = json.loads((backup_dir / "BACKUP_MANIFEST.json").read_text(encoding="utf-8"))
    files = manifest.get("files", [])
    if not files:
        raise ValueError("Empty backup manifest.")
    for item in files:
        rel = Path(item["path"])
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError("Unsafe manifest path.")
        file = backup_dir / rel
        if not file.is_file() or file.is_symlink():
            raise ValueError("Missing/unsafe backup file: " + item["path"])
        if file.stat().st_size != item["size"] or sha256(file) != item["sha256"]:
            raise ValueError("Modified backup file: " + item["path"])
    print("PASS_BACKUP_VERIFIED: %d files. Files match backup manifest." % len(files))
    print("Not proof of a bootable card or safe firmware installer.")
    return 0


def strip_outer_quotes(value):
    """Remove only a matching outer pair of quotes pasted from Explorer."""
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] == '"':
        return value[1:-1]
    return value


def interactive(args):
    """Python owns user input: CMD never interpolates space-containing paths."""
    base = Path(__file__).resolve().parent
    print("\nQVFilm SAFE PREFLIGHT v" + REPORT_VERSION)
    print("No camera/card writes. Original ML boot card must remain unchanged.")
    while True:
        print("\n1. Scan ORIGINAL JPG / CR2 firmware metadata")
        print("2. Back up known-good Magic Lantern card to PC")
        print("3. Verify SHA-256 backup manifest")
        print("4. Exit")
        print("5. Compatibility audit from JSON + optional CF/SD card")
        try:
            choice = input("Select 1-5: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExit. No card files modified.")
            return 0
        if choice == "4":
            return 0
        if choice not in ("1", "2", "3", "5"):
            print("Invalid choice.")
            continue
        try:
            if choice == "1":
                photo = strip_outer_quotes(input("Original JPG/CR2 path: "))
                if not photo:
                    print("Skipped scan: no original photo selected.")
                    continue
                card = strip_outer_quotes(input(
                    "Optional CF/SD card drive/folder (ENTER to skip): "))
                code = scan(argparse.Namespace(
                    photo=photo, card=card or None, out=str(base / "reports")))
            elif choice == "2":
                print("Card is read-only. Existing photos in DCIM are not backed up.")
                card = strip_outer_quotes(input(
                    "Existing known-good CF/SD card drive/folder: "))
                if not card:
                    print("Skipped backup: card path missing.")
                    continue
                dest = strip_outer_quotes(input(
                    "NEW nonexisting PC backup folder (NOT on the card): "))
                if not dest:
                    print("Skipped backup: destination missing.")
                    continue
                code = backup(argparse.Namespace(
                    card=card, dest=dest, max_gb=4))
            elif choice == "5":
                from compatibility_audit import review
                from pathlib import Path as PathCls
                default_report = base / "reports" / "qvfilm_preflight_report.json"
                report_path = strip_outer_quotes(input(
                    "Preflight JSON path (ENTER for reports/qvfilm_preflight_report.json): "))
                report_path = PathCls(report_path).expanduser().resolve() if report_path else default_report
                if not report_path.is_file():
                    print("BLOCKED: preflight JSON not found.")
                    continue
                card_input = strip_outer_quotes(input(
                    "Optional CF/SD card drive for READ-ONLY audit (ENTER to skip): "))
                if card_input:
                    card_root = PathCls(card_input).expanduser().resolve()
                    if is_inside(base, card_root):
                        print("BLOCKED: program folder appears to be on card; extract to PC.")
                        continue
                data = json.loads(report_path.read_text(encoding="utf-8"))
                result = review(data, card_input or None)
                output_dir = base / "reports"
                output_dir.mkdir(parents=True, exist_ok=True)
                outfile = output_dir / "qvfilm_compatibility_audit.json"
                outfile.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                                   encoding="utf-8")
                print("DECISION: ", result["installation_decision"])
                print("MPU candidate only (unverified): ",
                      result["public_firmware_candidate_from_community_mapping"])
                print("CARD: ", result["card_status"]["status"])
                print("Audit file: ", str(outfile))
                code = 0
            else:
                dest = strip_outer_quotes(input("PC backup folder to verify: "))
                if not dest:
                    print("Skipped verification: folder missing.")
                    continue
                code = verify_backup(argparse.Namespace(dir=dest))
            if code:
                print("CHECK NOT PASSED (code %s). No install permission." % code)
            else:
                print("Step finished. Does NOT grant permission to install firmware.")
        except (OSError, ValueError, RuntimeError,
                json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
            print("BLOCKED / ERROR: " + str(exc))
            print("No files written to the camera card.")


def main():
    parser = argparse.ArgumentParser(
        description="QVFilm 5D3.123 OFFLINE PREFLIGHT. No writes to camera/SD/CF.")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("interactive", help="Safe Windows interactive prompt; no CMD path parsing")
    p.set_defaults(func=interactive)
    p = sub.add_parser("scan", help="Read the original camera JPG/CR2 metadata")
    p.add_argument("--photo", required=True)
    p.add_argument("--card")
    p.add_argument("--out", default="reports")
    p.set_defaults(func=scan)
    p = sub.add_parser("backup", help="Backup existing ML files from a card to PC")
    p.add_argument("--card", required=True)
    p.add_argument("--dest", required=True)
    p.add_argument("--max-gb", type=float, default=4,
                   help="Refuse very large ML directory; default 4 GB")
    p.set_defaults(func=backup)
    p = sub.add_parser("verify-backup", help="Verify SHA-256 manifest of backup")
    p.add_argument("--dir", required=True)
    p.set_defaults(func=verify_backup)
    args = parser.parse_args()
    try:
        return args.func(args)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print("BLOCKED: " + str(e), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
