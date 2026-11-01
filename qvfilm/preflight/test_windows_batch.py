#!/usr/bin/env python3
"""Real Windows cmd.exe smoke test for QVFilm hotfix; uses dummy files, no camera."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    if os.name != "nt":
        print("Windows-only smoke test skipped.")
        return 0

    src = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix="QVFILM_") as scratch:
        root = Path(scratch) / "5D Mark III Upgrade"
        prog = root / "QVFILM_5D3_WIN10_PREFLIGHT_RECOVERY_v0.2.1_NOT_INSTALLABLE"
        prog.mkdir(parents=True)
        for name in ("preflight.py", "QVFILM_START_WIN10.cmd"):
            shutil.copy2(src / name, prog / name)

        image = root / "Photo" / "_C2A8994.JPG"
        image.parent.mkdir()
        image.write_bytes(b"dummy EXIF-free image for CMD argument smoke test")
        card = root / "Card Source G"   # fake card, not an actual drive
        (card / "ML" / "MODULES").mkdir(parents=True)
        (card / "autoexec.bin").write_bytes(b"dummy known good boot content")
        (card / "ML" / "MODULES" / "mlv_lite.mo").write_bytes(b"dummy module")
        original_contents = (card / "autoexec.bin").read_bytes()
        backup = root / "PC Backup With Spaces"

        # This mimics the real screenshot: program under "...5D Mark III Upgrade",
        # original photo under "...Photo", optional card path, backup + verify.
        input_text = "\n".join([
            "1", str(image), str(card),
            "2", str(card), str(backup),
            "3", str(backup),
            "4", "",
        ])
        env = os.environ.copy()
        env["QVFILM_NO_PAUSE"] = "1"
        # cmd.exe executes a path containing spaces; all user paths go directly
        # to Python input(), not as concatenated CMD arguments.
        cp = subprocess.run(
            ["cmd.exe", "/d", "/c", 'call "%s"' % (prog / "QVFILM_START_WIN10.cmd")],
            cwd=str(prog),
            input=input_text,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=45,
            check=False,
        )
        print(cp.stdout[-3500:])
        if cp.stderr:
            print(cp.stderr[-1200:], file=sys.stderr)
        assert cp.returncode == 0, "CMD wrapper exit code: %s" % cp.returncode
        assert "unrecognized arguments" not in cp.stdout + cp.stderr
        assert "usage: preflight.py" not in cp.stdout + cp.stderr

        report_file = prog / "reports" / "qvfilm_preflight_report.json"
        assert report_file.is_file(), "Report not created in space-containing program path"
        report = json.loads(report_file.read_text(encoding="utf-8"))
        assert report["status"] == "REVIEW_REQUIRED", report
        assert "ExifTool missing" in report["reason"], report
        assert (backup / "BACKUP_COMPLETE.txt").is_file(), "Backup incomplete"
        assert (backup / "BACKUP_MANIFEST.json").is_file(), "No backup manifest"
        assert (card / "autoexec.bin").read_bytes() == original_contents
        assert not (card / "BACKUP_COMPLETE.txt").exists()
        print("PASS: Windows CMD + spaces in input/prog/card/backup paths; report+SHA verification")

    return 0


if __name__ == "__main__":
    sys.exit(main())
