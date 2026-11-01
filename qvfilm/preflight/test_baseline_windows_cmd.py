"""Smoke-test the baseline staging CMD on real Windows GitHub runner (no camera)."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def main():
    if os.name != "nt":
        print("SKIP: Windows-specific test.")
        return 0
    here = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "5D Mark III Upgrade"
        program = root / "QVFILM Stage v0.3.0"
        program.mkdir(parents=True)
        for file in ("baseline_stager.py", "QVFILM_BASELINE_CHECK_WIN10.cmd"):
            shutil.copy2(here / file, program / file)
        source = root / "Incoming ZIP with spaces"
        source.mkdir()
        archive = source / "magiclantern-5D3.123.zip"
        with zipfile.ZipFile(archive, "w") as z:
            z.writestr("autoexec.bin", b"not firmware")
            z.writestr("ML-SETUP.FIR", b"not firmware")
            z.writestr("ML/MODULES/test.mo", b"not firmware")
        env = os.environ.copy()
        env["QVFILM_NO_PAUSE"] = "1"
        run = subprocess.run(
            ["cmd.exe", "/d", "/c", str(program / "QVFILM_BASELINE_CHECK_WIN10.cmd")],
            cwd=str(program), input='"' + str(archive) + '"\n', text=True,
            capture_output=True, encoding="utf-8", errors="replace",
            timeout=45, env=env)
        print(run.stdout[-2500:])
        assert run.returncode == 0, (run.returncode, run.stderr)
        manifest = program / "reports" / "qvfilm_baseline_stage.json"
        assert manifest.is_file()
        result = json.loads(manifest.read_text(encoding="utf-8"))
        assert result["decision"] == "STRUCTURE_PASS_INSTALL_HOLD"
        assert archive.is_file()
        assert not (program / "autoexec.bin").exists()
        print("PASS: Windows baseline staging CMD + ZIP paths with spaces; no camera/card writes")


if __name__ == "__main__":
    sys.exit(main())
