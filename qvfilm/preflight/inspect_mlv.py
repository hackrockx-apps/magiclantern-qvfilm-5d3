#!/usr/bin/env python3
"""QVFilm v0.4.0 minimal .MLV integrity precheck (PC-only, no media writes).

Only checks file presence, first four bytes, filesize, and SHA256.
Cannot detect dropped frames, decode video, or prove correctness of recordings.
SPDX-License-Identifier: GPL-2.0-or-later
"""
import argparse
import hashlib
import json
from pathlib import Path

SIGNATURE = b"MLVI"


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def inspect(path):
    path = Path(path).expanduser().resolve()
    output = {
        "tool": "QVFilm MLV offline first-take inspector v0.4.0",
        "filename": path.name,
        "status": "REJECT",
        "has_mlvi_signature": False,
        "file_size_bytes": None,
        "file_sha256": None,
        "note": "Header signature/size/hash do not verify playback, frame integrity, or dropped frames.",
    }
    if not path.is_file() or path.suffix.lower() != ".mlv":
        output["reason"] = "Select an existing .MLV file copied to the PC."
        return output
    size = path.stat().st_size
    output["file_size_bytes"] = size
    if size < 128:
        output["reason"] = "File too small for a plausible MLV recording."
        return output
    with path.open("rb") as f:
        magic = f.read(4)
    output["has_mlvi_signature"] = magic == SIGNATURE
    output["file_sha256"] = sha256(path)
    if magic != SIGNATURE:
        output["reason"] = "MLVI signature missing. It is not a recognized base MLV file."
        return output
    output["status"] = "BASIC_FILE_CHECK_PASS"
    output["reason"] = "MLVI header signature present and SHA-256 measured; playback not validated."
    return output


def main():
    p = argparse.ArgumentParser(description="Inspect an MLV copied to PC, never write to camera card.")
    p.add_argument("--mlv", help="Path to .MLV file copied to PC")
    p.add_argument("--out", help="PC report path")
    args = p.parse_args()
    file = args.mlv.strip().strip('"') if args.mlv else input("Path to MLV copied to PC: ").strip().strip('"')
    if not file:
        print("No file supplied.")
        return 2
    result = inspect(file)
    report = (Path(args.out).expanduser().resolve() if args.out else
              Path(__file__).resolve().parent / "reports" / "qvfilm_mlv_first_take.json")
    if report == Path(file).expanduser().resolve():
        p.error("Cannot overwrite source MLV.")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("MLV RESULT:", result["status"])
    print(result["reason"])
    print("Report:", report)
    print("Check actual video frames in MLV App before claiming RAW recording PASS.")
    return 0 if result["status"] == "BASIC_FILE_CHECK_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
