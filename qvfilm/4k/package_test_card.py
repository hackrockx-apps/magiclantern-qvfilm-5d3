#!/usr/bin/env python3
"""Stage an isolated, SAME-COMMIT 5D3.123 4K engineering pilot package.

Does not write camera media, change boot flags or produce Canon .FIR files.
The staged CARD_ROOT is for future controlled TEST-card validation only.
No 4K FPS, preview smoothness or record stability is implied by a clean build.

From checked-out repository after CI has built Core + modules:
    python3 qvfilm/4k/package_test_card.py --out dist/qvfil-4k-review

All content is taken from the current source tree, never the previous
QVFIL 2025 branch, another download or an installed camera card.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HARDWARE_STATUS = "UNTESTED -- NOT APPROVED FOR CAMERA INSTALLATION"
REQUIRED = {
    "platform/5D3.123/autoexec.bin": "CARD_ROOT/autoexec.bin",
    "platform/5D3.123/5D3_123.sym": "CARD_ROOT/ML/MODULES/5D3_123.SYM",
    "modules/crop_rec/crop_rec.mo": "CARD_ROOT/ML/MODULES/CROP_REC.MO",
    "modules/mlv_lite/mlv_lite.mo": "CARD_ROOT/ML/MODULES/MLV_LITE.MO",
}
SAFETY_ANCHORS = {
    "modules/crop_rec/crop_rec.c": [
        'CONFIG_INT("crop.preset", crop_preset_index, 0);',
        '"UHD 1:1"',
        '"1:1 4K UHD crop (3840x1600 @ 24p, square raw pixels, preview broken)',
    ],
    "modules/mlv_lite/mlv_lite.c": [
        'CONFIG_INT("raw.video.enabled", raw_video_enabled, 0);',
        'CONFIG_INT("raw.output_format", output_format, 2);',
        'CONFIG_INT("raw.more.hacks", more_hacks, 0);',
        'CONFIG_INT("raw.CropRecPreview", prevmode, 0);',
        'CONFIG_INT("raw.use.srm.memory", use_srm_memory, 0);',
        'CONFIG_INT("raw.small.hacks", small_hacks, 0);',
        'CONFIG_INT("raw.card_spanning", card_spanning, 0);',
        'raw_preview_fast_ex2(',
        'CHOICES("legacy", "ultrafast")',
    ],
    "src/raw.c": ["FRAMED_PREVIEW_PARAM__ENGINE__ULTRAFAST", "raw_preview_fast_ex2("],
    "src/module.c": ['char *core_modules[] = {"mlv_play", "mlv_snd", "sd_uhs", "lua", "file_man", "dual_iso", "silent", "ettr", "focus_sq"};',
                     "if(!config_flag_file_setting_load(enable_file) && index_in_core_modules >= core_modules_count)"],
}

WARNINGS = """QVFIL 4K CINEMA -- 5D3.123 -- EXPERIMENTAL REVIEW PACKAGE

NOT APPROVED FOR CAMERA INSTALLATION UNTIL A HUMAN REVIEWS THIS PACKAGE.
THE CAMERA HAS NOT BEEN TESTED WITH THESE BUILD OUTPUTS.

The payload lives under CARD_ROOT, intentionally not at ZIP top level.
This ZIP is not a drag-and-drop update, not a Canon firmware update and
not a working 'QVFIL 4K Stable' release. Nothing is flashed by this script.

A future controlled pilot MUST use a separately prepared, known-bootable,
empty TEST card compatible with EOS 5D Mark III Canon firmware 1.2.3.
Never replace files on the only known-good Magic Lantern card.
Never mix this autoexec.bin/5D3_123.SYM/crop_rec.mo/mlv_lite.mo with
ML 2025 or QVFIL 0.6.x binary modules, CFG files or outdated firmware.

This is the Danne/Arnaud-derived 4K code base, WITHOUT the prior QVFIL HUD.
Its source label 'UHD 1:1' documents 3840x1600@24, NOT 3840x2160.
Its crop preview is documented as 'broken'; Ultrafast may or may not help.
Its fresh-card defaults: crop OFF, RAW OFF, card spanning OFF,
More Hacks OFF, Small Hacks OFF, SRM memory OFF, CropRecPreview OFF,
10-bit uncompressed. Enabling modules still initializes background
tasks including the compression task. BOOT/RECORD IS UNTESTED.
Recorder/Crop are NOT core auto-load modules in this pilot, so a fresh\nclean card must require manual opt-in from Modules before they initialize.\nA correct ZIP/SHA256 is NOT a camera safety approval.
Selecting 4K, enabling recording or altering preview is a separate
explicit opt-in and requires STOP at first abnormal response.

Do not attempt Canon firmware flash, boot flag modification, or install
the ML-SETUP.FIR using this pack. It is deliberately NOT included.
4K RAW 10b 3840x1600@24 needs ~184.3 decimal MB/s uncompressed;
recording requires actual measured, sustainable card + compression capacity.

After any pilot: verify file RAWI width/height, MLVI fps, VIDF frame
continuity with qvfilm/4k/mlv_audit.py and visually decode with MLV App.
PASS source build and pass metadata do not imply clean frames or live preview.
"""

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def fail(message: str):
    raise RuntimeError(message)

def stage(root: Path, out: Path, revision: str, *, allow_synthetic=False) -> dict:
    if out.exists():
        fail(f"Refusing to overwrite existing package: {out}")
    if not allow_synthetic:
        for path,anchors in SAFETY_ANCHORS.items():
            source=(root/path)
            if not source.is_file():
                fail(f"Missing source: {source}")
            text=source.read_text(encoding="utf-8")
            for anchor in anchors:
                if anchor not in text:
                    fail(f"Safety/source invariant missing in {path}: {anchor}")
    inputs={}
    for src,dst in REQUIRED.items():
        srcfile=root/src
        if not srcfile.is_file() or srcfile.stat().st_size==0:
            fail(f"Required same-tree build output missing/empty: {srcfile}")
        inputs[dst]=srcfile
    groups=(
        ("data/fonts","*.rbf","CARD_ROOT/ML/FONTS",4),
        ("data/vram","*.lut","CARD_ROOT/ML/DATA",4),
        ("data/cropmks","*.bmp","CARD_ROOT/ML/CROPMKS",1),
    )
    for srcdir,pattern,dst,count in groups:
        files=sorted((root/srcdir).glob(pattern))
        if len(files)<count:fail(f"{srcdir} expected >= {count} files, found {len(files)}")
        for src in files:
            dstfile=f"{dst}/{src.name}"
            if dstfile in inputs:fail(f"Name collision: {dstfile}")
            inputs[dstfile]=src
    payload=out/"CARD_ROOT"
    # Stage read-only in a dedicated directory, never directly onto a card.
    for relative,src in sorted(inputs.items()):
        destination=out/relative
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(src,destination)
        if sha256(src)!=sha256(destination):
            fail(f"Copy hash mismatch: {src}")
    manifest={
        "label":"QVFIL 4K CINEMA – 5D3.123 engineering test-card review",
        "status":HARDWARE_STATUS,
        "git_revision":revision,
        "canon_target":"5D3.123 (Canon firmware 1.2.3; NOT internal Magic Lantern ID property)",
        "source_family":"Danne/Arnaud-derived 4K tree, not ML2025",
        "camera_installation_approved":False,
        "not_included":["ML-SETUP.FIR","AUTOEXEC.FIR","CONFIG.CFG",
                        "QVFILL_2025_MLV_LITE.MO","old QVFIL HUD"],
        "observations_not_verified":["native sensor readout","4K MLV frames",
                                     "24p continuous recording","CF speed",
                                     "true color 4K STBY/REC preview",
                                     "battery/thermal safety"],
        "files":{key:{"bytes":(out/key).stat().st_size,"sha256":sha256(out/key)}
                 for key in sorted(inputs)},
    }
    (out/"MANIFEST.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    (out/"READ_ME_FIRST.txt").write_text(WARNINGS,encoding="utf-8")
    handbook=root/"qvfilm/4k/USER_TEST_PROTOCOL_VI.md"
    if handbook.is_file():
        shutil.copyfile(handbook,out/"USER_TEST_PROTOCOL_VI.md")
    checksum_lines=[f'{h["sha256"]}  {name}' for name,h in manifest["files"].items()]
    (out/"SHA256SUMS.txt").write_text("\n".join(checksum_lines)+"\n",encoding="utf-8")
    # Zip includes CARD_ROOT and reports, NOT a deceptive ready-to-run root.
    archive=out.parent/(out.name+".zip")
    if archive.exists():fail(f"Refusing to overwrite archive: {archive}")
    with zipfile.ZipFile(archive,"w",compression=zipfile.ZIP_DEFLATED,
                         compresslevel=6,allowZip64=True) as z:
        for dirname in ("CARD_ROOT/ML/SETTINGS/", "CARD_ROOT/ML/LOGS/"):
            z.writestr(dirname,b"")
        for f in sorted(p for p in out.rglob("*") if p.is_file()):
            z.write(f,f.relative_to(out))
    with zipfile.ZipFile(archive) as z:
        if z.testzip():fail("ZIP CRC integrity check failed")
        names=set(z.namelist())
        if "autoexec.bin" in names or "ML-SETUP.FIR" in names:
            fail("Unsafe zip-root or firmware installer inclusion")
        if not {"CARD_ROOT/autoexec.bin","CARD_ROOT/ML/MODULES/CROP_REC.MO",
                "CARD_ROOT/ML/MODULES/MLV_LITE.MO",
                "CARD_ROOT/ML/MODULES/5D3_123.SYM"}.issubset(names):
            fail("Incomplete pilot package")
        # Verify hashes of files INSIDE the zip itself (not just source).
        for name,info in manifest["files"].items():
            digest=hashlib.sha256(z.read(name)).hexdigest()
            if digest!=info["sha256"]:
                fail(f"Archive hash mismatch: {name}")
    return {"archive":str(archive),"archive_sha256":sha256(archive),
            "files":len(inputs),"revision":revision,
            "hardware_tested":False,"camera_installable_approval":False}

def main():
    p=argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out",type=Path,default=Path("dist/qvfil-4k-review"))
    args=p.parse_args()
    try:
        revision=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,
                                          text=True).strip()
        result=stage(ROOT,args.out.resolve(),revision)
        print(json.dumps(result,indent=2))
    except (RuntimeError,subprocess.CalledProcessError) as e:
        p.exit(2,f"FAILED CLOSED: {e}\n")

if __name__=="__main__":
    main()
