#!/usr/bin/env python3
"""QVFilm v0.4.3: read-only triage of copied Magic Lantern text logs on a PC.

Does not read/write camera devices, update any .MO/.FIR, or decide install safety.
Never uploads logs. Place copies in a local PC directory, not on the SD/CF card.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

PATTERNS = {
    "lossless_return": re.compile(r"Compression error\s+(-\d+)\s+at\s+frame\s+(\d+)", re.I),
    "mlv_assert": re.compile(r"(?:ML\s+)?ASSERT.*mlv_lite\.c\s*:\s*2742|mlv_lite\.c\s*:\s*2742", re.I),
    "compress_task": re.compile(r"compress_task", re.I),
    "card_warning": re.compile(r"(?:EDMAC timeout|buffer full|dropped frames?|card too slow)", re.I),
}
LOSSLESS_RETURNS = {
    -1: "encoder not initialized / missing required hardware resources",
    -2: "compression completion semaphore timed out",
    -3: "compressed output did not contain expected JPEG signature",
}


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as inp:
        for chunk in iter(lambda: inp.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def triage_file(path):
    path = Path(path).expanduser().resolve()
    if not path.is_file() or path.suffix.lower() not in {".log", ".txt"}:
        raise ValueError("Select a copied .LOG/.TXT file on the PC.")
    if path.stat().st_size > 12 * 1024 * 1024:
        raise ValueError("Log too large for safe minimal parsing.")
    text = path.read_text(encoding="utf-8", errors="replace")
    findings = []
    for index, line in enumerate(text.splitlines(), 1):
        matched = [name for name, pattern in PATTERNS.items() if pattern.search(line)]
        if not matched:
            continue
        code = PATTERNS["lossless_return"].search(line)
        item = {"line": index, "kinds": matched}
        if code:
            number = int(code.group(1))
            item.update({"compression_error": number, "frame": int(code.group(2)),
                         "interpretation": LOSSLESS_RETURNS.get(number, "unknown negative return")})
        findings.append(item)
        if len(findings) >= 500:
            break
    return {
        "file_name": path.name,
        "file_sha256": digest(path),
        "file_size": path.stat().st_size,
        "findings": findings,
        "contains_compression_return_code": any("compression_error" in x for x in findings),
        "note": "No raw log content exported; absence of matches does not rule out a camera crash.",
    }


def main():
    parser = argparse.ArgumentParser(description="QVFilm offline ML log triage (PC-copy only)")
    parser.add_argument("--folder", required=True, help="Folder on PC containing copied log files")
    parser.add_argument("--out", required=True, help="JSON output on PC, never camera card")
    args = parser.parse_args()
    folder = Path(args.folder).expanduser().resolve()
    dest = Path(args.out).expanduser().resolve()
    if not folder.is_dir():
        parser.error("Log folder not found.")
    if dest == folder or folder in dest.parents:
        parser.error("Output must be outside input folder to avoid mixing originals and reports.")
    logs = [p for p in sorted(folder.iterdir()) if p.is_file() and p.suffix.lower() in (".log", ".txt")]
    if not logs:
        parser.error("No .LOG/.TXT files. Copy original log(s) from the camera card to a PC folder first.")
    report = {
        "tool": "QVFilm ML Log Triage v0.4.3",
        "status": "DIAGNOSIS_ONLY",
        "source": "COPIED_LOGS_ON_PC",
        "logs": [triage_file(file) for file in logs[:80]],
        "warnings": [
            "The code -1/-2/-3 applies only if an explicit Compression error line is actually present.",
            "No conclusion about hardware, card, or lossless bug from a missing error code.",
            "Do not install a new firmware/module just because this report parses.",
        ],
    }
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Read-only diagnosis saved:", dest)
    print("Matching log files:", sum(bool(x["findings"]) for x in report["logs"]))
    print("Do not modify Magic Lantern firmware based solely on this report.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
