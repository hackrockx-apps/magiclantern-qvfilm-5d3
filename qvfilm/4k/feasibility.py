#!/usr/bin/env python3
"""Offline 5D Mark III 4K RAW / CF throughput feasibility analysis.

Never makes camera register changes. A source-level preflight aid only.
RAW input byte rates exclude MLV headers, file system stalls, card-speed
variability, LJ92 CPU time, and buffer scheduling. Bit packing is idealized;
check effective BPP from actual MLV after any camera test.

Usage:
  python3 qvfilm/4k/feasibility.py --write-mb-s 100
  python3 qvfilm/4k/feasibility.py --write-mb-s 120 --headroom 0.20
  python3 qvfilm/4k/feasibility.py --write-mb-s 145 --compression 1.7 --json
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

@dataclass(frozen=True)
class Mode:
    label: str
    width: int
    height: int
    fps: float
    bitdepth: int
    caveat: str

# The first two are 4K-WIDTH CINEMASCOPE, NOT UHD 3840x2160.
# Mode names represent desired MLV frame dimensions, NOT a statement
# that this source tree will achieve these for every crop_rec preset.
MODES = (
    Mode("4K-wide 2.40:1 cinema", 3840, 1600, 24, 10,
         "ML experimental 1:1 crop; non-UHD; preview may be broken"),
    Mode("4K-wide 2.84:1 scope", 4096, 1440, 25, 10,
         "Historical experimental mode; verify branch-specific sensor FPS"),
    Mode("3K fallback 1:1", 3072, 1920, 24, 10,
         "Not 4K; valuable to verify 1:1 crop and RAW pipeline"),
    Mode("UHD 16:9 research", 3840, 2160, 25, 10,
         "NOT established as continuous 25p on 5D3, do not promise"),
    Mode("UHD 16:9 research 14b", 3840, 2160, 24, 14,
         "NOT established; heavy RAM/encoder/storage demands"),
    Mode("4K half-rate experiment", 4096, 2560, 12.5, 10,
         "Not motion-picture 24/25p, mode may require preview workaround"),
)

def rate_mb_s(mode: Mode, compression: float = 1.0) -> float:
    """Decimal MB/s idealized packed RAW. No sensor/firmware guarantee."""
    if compression < 1:
        raise ValueError("compression ratio must be >= 1")
    return mode.width * mode.height * mode.fps * mode.bitdepth / 8 / 1e6 / compression

def required_ratio(mode: Mode, sustained_write_mb_s: float, headroom: float = 0.20) -> float:
    """Compression ratio required so payload <= (1-headroom)*sustained-write."""
    if sustained_write_mb_s <= 0:
        raise ValueError("write speed must be positive")
    if not 0 <= headroom < 1:
        raise ValueError("headroom must be in [0,1)")
    return rate_mb_s(mode) / (sustained_write_mb_s * (1-headroom))

def evaluate(mode: Mode, write_mb_s: float, headroom: float, compression: float) -> dict:
    effective = rate_mb_s(mode, compression)
    cap = write_mb_s * (1-headroom)
    return {
        **asdict(mode),
        "uncompressed_mb_s": round(rate_mb_s(mode),2),
        "modeled_after_compression_mb_s": round(effective,2),
        "sustained_write_budget_mb_s": round(cap,2),
        "required_compression_ratio": round(required_ratio(mode,write_mb_s,headroom),2),
        "modeled_storage_margin_mb_s": round(cap-effective,2),
        "within_modeled_storage_budget": effective <= cap,
        "NOT_A_CAMERA_VALIDATION": True,
    }

def main():
    p=argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--write-mb-s",type=float,default=100,
        help="Measured sustained write speed ON CAMERA, not card label (default 100 is illustrative)")
    p.add_argument("--headroom",type=float,default=0.20,
        help="Reserve fraction for write stalls / file overhead (default 0.20)")
    p.add_argument("--compression",type=float,default=1.0,
        help="Illustrative lossless compression ratio, NOT guaranteed (default 1)")
    p.add_argument("--json",action="store_true")
    args=p.parse_args()
    if args.write_mb_s <= 0 or args.compression < 1 or not 0 <= args.headroom < 1:
        p.error("require write>0, compression>=1 and 0<=headroom<1")
    rows=[evaluate(m,args.write_mb_s,args.headroom,args.compression) for m in MODES]
    if args.json:
        print(json.dumps({
            "assumption":"Sustained write input is an illustration until MEASURED on this camera",
            "modeled_write_mb_s":args.write_mb_s,
            "compression_ratio_not_guaranteed":args.compression,
            "reserved_headroom":args.headroom,
            "modes":rows,
        },ensure_ascii=False,indent=2))
    else:
        print("5D3 RAW bandwidth model: hypothetical write %.1f MB/s, %.0f%% reserve, %.2fx compression" %
              (args.write_mb_s,args.headroom*100,args.compression))
        print("NO claim of functional crop mode, fps, compression stability, or LCD rate")
        print("%-29s %8s %8s %8s %8s %6s" %
              ("MODE","RAW MB/s","AFTER","BUDGET","RATIO", "FIT?"))
        for row in rows:
            print("%-29s %8.1f %8.1f %8.1f %8.2fx %6s" % (
                row["label"],row["uncompressed_mb_s"],
                row["modeled_after_compression_mb_s"],
                row["sustained_write_budget_mb_s"],
                row["required_compression_ratio"],
                "YES*" if row["within_modeled_storage_budget"] else "NO"))
        print("*YES means storage model only; no guarantee of source 4K mode, thermals, buffer, or preview.")

if __name__=="__main__":
    main()
