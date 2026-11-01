#!/usr/bin/env python3
"""QVFilm 5D3.123 baseline SHA256 provenance check, PC-only.

The expected digest was transcribed from the official Magic Lantern
5D3.123 build page *screenshot supplied by the operator*. The tool
compares the prior local inspection report against that published value.
No installation authorization is ever issued.
"""
import argparse
import json
from pathlib import Path

EXPECTED_FILENAME = "magiclantern.2025-06-20.5D3.123.zip"
EXPECTED_SHA256 = "63ca9e56405573ce58f9fca2680d17bb87ce57a5b946f66afc2cbb16ccf00d77"
EXPECTED_PLATFORM = "5D3.123"


def verify(report):
    if not isinstance(report, dict):
        raise ValueError("JSON root must be a dictionary.")
    structure = report.get("structure") or {}
    if not isinstance(structure, dict):
        structure = {}
    checks = {
        "filename_exact": report.get("source_filename") == EXPECTED_FILENAME,
        "sha256_matches_magic_lantern_page_screenshot": (
            str(report.get("source_sha256", "")).lower() == EXPECTED_SHA256
        ),
        "platform_exact": report.get("target") == EXPECTED_PLATFORM,
        "zip_readable": report.get("archive_readable") is True,
        "stage_structure_pass": report.get("decision") == "STRUCTURE_PASS_INSTALL_HOLD",
        "autoexec_present": structure.get("autoexec_present") is True,
        "setup_fir_present": structure.get("setup_fir_present") is True,
        "ml_files_present": isinstance(structure.get("ml_file_count"), int)
                            and structure.get("ml_file_count") > 0,
        "no_missing_required": structure.get("missing_required") == [],
        "no_unexpected_root_firmware": structure.get("unexpected_root_firmware_bins") == [],
    }
    ok = all(checks.values())
    return {
        "version": "0.3.1",
        "camera": "Canon EOS 5D Mark III",
        "candidate_platform": EXPECTED_PLATFORM,
        "source_evidence": "Magic Lantern build page screenshot supplied by operator",
        "expected_filename": EXPECTED_FILENAME,
        "expected_sha256": EXPECTED_SHA256,
        "observed_filename": report.get("source_filename"),
        "observed_sha256": report.get("source_sha256"),
        "checks": checks,
        "baseline_zip_decision": ("CHECKSUM_AND_STRUCTURE_MATCH"
                                   if ok else "CHECKSUM_OR_STRUCTURE_MISMATCH"),
        "canon_public_firmware_1_2_3_independently_verified": False,
        "installer_bootflag_recovery_reviewed": False,
        "installation_decision": "DO_NOT_INSTALL",
        "next_gate": (
            "Independently confirm camera public firmware is exactly Canon 1.2.3; "
            "do not infer installation permission from MPU 9.0.1/A6 or from SHA256 match."
        ),
        "note": (
            "This verification checks an operator-generated JSON. It does NOT independently "
            "read the ZIP bytes or authenticate the upstream website. Use SHA256 verification "
            "on the source ZIP and physical checks prior to any installation."
        ),
    }


def main():
    p = argparse.ArgumentParser(description="QVFilm baseline source check; PC only")
    p.add_argument("--report", required=True, help="v0.3.0 qvfilm_baseline_stage.json")
    p.add_argument("--out", help="Output path on PC; defaults to reports/qvfilm_source_audit.json")
    args = p.parse_args()
    report = Path(args.report).expanduser().resolve()
    if not report.is_file():
        p.error("Baseline report file not found.")
    data = verify(json.loads(report.read_text(encoding="utf-8")))
    dest = (Path(args.out).expanduser().resolve() if args.out
            else Path(__file__).resolve().parent / "reports" / "qvfilm_source_audit.json")
    if dest == report:
        p.error("Output must not overwrite source report.")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    print("QVFILM BASELINE:", data["baseline_zip_decision"])
    print("INSTALLATION:", data["installation_decision"])
    print("Audit:", str(dest))
    return 0 if data["baseline_zip_decision"] == "CHECKSUM_AND_STRUCTURE_MATCH" else 2


if __name__ == "__main__":
    raise SystemExit(main())
