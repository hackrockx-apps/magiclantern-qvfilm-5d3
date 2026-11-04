#!/usr/bin/env python3
"""Read-only MLV/M00/M01... structural verification for QVFIL 4K pilot.

This program does NOT decompress video pixels or certify correct sensor crop.
It scans MLV block headers, reports source frame rate, RAWI resolution,
video frame-number continuity, trailer integrity and file flags. Full visual
MLV App review still required before calling any 4K clip stable.

Accept paths to all chunks of ONE clip, e.g.
  python3 qvfilm/4k/mlv_audit.py MVI_0001.MLV MVI_0001.M00 MVI_0001.M01
  python3 qvfilm/4k/mlv_audit.py --json MVI_0001.MLV MVI_0001.M00
"""
from __future__ import annotations
import argparse
import json
import struct
from pathlib import Path

HEADER_MIN=16
MAX_BLOCK_SIZE=2**31 # protect invalid bogus offsets
KNOWN={b"MLVI",b"VIDF",b"RAWI",b"RAWC",b"AUDF",b"WAVI",b"IDNT",
       b"LENS",b"EXPO",b"WBAL",b"RTCI",b"STYL",b"INFO",b"DEBG",
       b"VERS",b"MARK",b"NULL",b"DISO",b"ELVL",b"SYNC",b"XREF",
       b"BKUP",b"LOGM",b"GPSD"}

def inspect_one(path):
    size=path.stat().st_size
    summary={
        "file":str(path),"bytes":size,"headers":[],"raw_dimensions":[],
        "frame_numbers":[],"video_timestamps_us":[],"audio_frames":0,
        "blocks":0,"errors":[],"unknown_types":{},
    }
    with path.open("rb") as f:
        offset=0
        while offset<size:
            if size-offset<HEADER_MIN:
                summary["errors"].append("Trailing short header at byte "+str(offset))
                break
            f.seek(offset)
            buf=f.read(HEADER_MIN)
            kind,length,stamp=struct.unpack("<4sIQ",buf)
            if length<HEADER_MIN or length>MAX_BLOCK_SIZE or length>size-offset:
                summary["errors"].append(
                    f"Invalid/incomplete {kind!r} block size {length} at byte {offset}")
                break
            summary["blocks"]+=1
            if kind not in KNOWN:
                name=kind.decode("ascii",errors="replace")
                summary["unknown_types"][name]=summary["unknown_types"].get(name,0)+1
            if kind==b"MLVI":
                if length<60:
                    summary["errors"].append(f"MLVI header too short ({length})")
                else:
                    f.seek(offset+16)
                    b=f.read(44)
                    # MLVI v2: versionString[8], fileGuid[8], fileNum/count,
                    # flags[4], video/audioClass[2 each], frameCount [4 each],
                    # sourceFpsNom/Denom [4 each].
                    v,guid,file_num,file_count,flags,vc,ac,vf,af,nom,den=\
                        struct.unpack("<8sQHHIHHIIII",b)
                    summary["headers"].append({
                        "version":v.rstrip(b"\x00").decode("ascii","replace"),
                        "file_guid":guid, "part":file_num, "part_count":file_count,
                        "flags":flags, "recording_error_flag":bool(flags&8),
                        "dropped_frames_flag":bool(flags&2),
                        "video_class":vc,"audio_class":ac,
                        "announced_video_frames":vf,"fps":nom/den if den else None
                    })
            elif kind==b"RAWI":
                if length>=20:
                    f.seek(offset+16)
                    w,h=struct.unpack("<HH",f.read(4))
                    summary["raw_dimensions"].append([w,h])
            elif kind==b"VIDF":
                if length>=32:
                    f.seek(offset+16)
                    number,cx,cy,px,py,pad=struct.unpack("<IHHHHI",f.read(16))
                    summary["frame_numbers"].append(number)
                    summary["video_timestamps_us"].append(stamp)
                    if pad>length-32:
                        summary["errors"].append(
                            f"VIDF frame {number}: frameSpace {pad} exceeds payload at byte {offset}")
                else:
                    summary["errors"].append(f"Short VIDF block at byte {offset}")
            elif kind==b"AUDF":
                summary["audio_frames"]+=1
            offset+=length
        summary["scanned_bytes"]=offset
    return summary

def inspect(files):
    parts=[inspect_one(Path(x)) for x in files]
    all_heads=[h for p in parts for h in p["headers"]]
    all_dims=sorted({tuple(d) for p in parts for d in p["raw_dimensions"]})
    fps=sorted({round(h["fps"],3) for h in all_heads if h["fps"]})
    all_nums=sorted(n for p in parts for n in p["frame_numbers"])
    missing=0
    if all_nums:
        # Compare contiguous frame numbers globally, not file length.
        missing=(all_nums[-1]-all_nums[0]+1)-len(set(all_nums))
    repeated=len(all_nums)-len(set(all_nums))
    guids={h["file_guid"] for h in all_heads}
    part_nums=[h["part"] for h in all_heads]
    claims=[h["part_count"] for h in all_heads if h["part_count"]]
    errors=[f'{p["file"]}: {error}' for p in parts for error in p["errors"]]
    if len(guids)>1: errors.append("MLVI file GUID mismatch across chunks")
    if repeated: errors.append(f"Duplicate video frame numbers: {repeated}")
    if missing: errors.append(f"Missing frame numbers in observed range: {missing}")
    if any(h["recording_error_flag"] for h in all_heads):
        errors.append("MLVI recording error flag set in at least one part")
    if any(h["dropped_frames_flag"] for h in all_heads):
        errors.append("MLVI dropped-frames flag set in at least one part")
    if any(x==0 for x in claims):
        errors.append("Invalid file part count 0")
    if len(set(part_nums))!=len(part_nums):
        errors.append("Duplicate MLVI chunk part indices")
    if len(fps)>1: errors.append("Conflicting MLVI nominal frame rates")
    if len(all_dims)>1: errors.append("Conflicting RAWI frame resolutions")
    if not all_heads: errors.append("Missing MLVI main header")
    if not all_dims: errors.append("Missing RAWI header / no resolution evidence")
    if not all_nums: errors.append("No VIDF frames")
    return {
        "result":"STRUCTURE_PASS" if not errors else "STRUCTURE_FAIL",
        "files":len(parts),
        "input_mb":round(sum(p["bytes"] for p in parts)/1e6,2),
        "mlvi_guid":next(iter(guids)) if len(guids)==1 else None,
        "rawi_resolutions":[list(d) for d in all_dims],
        "is_true_uhd_3840x2160":all_dims==[(3840,2160)],
        "is_true_4k_width":bool(all_dims) and all(w>=3840 for w,h in all_dims),
        "declared_fps":fps,
        "observed_vidf_frames":len(all_nums),
        "missing_frame_numbers":missing,
        "duplicated_frame_numbers":repeated,
        "mlvi_flags":[h["flags"] for h in all_heads],
        "errors":errors,
        "IMPORTANT":"Structure PASS != decoded pixel integrity, exposure, rolling shutter, smooth LCD, sustained recording or true sensor 1:1 readout. Inspect in MLV App and test each source crop mode.",
        "parts":[{k:v for k,v in p.items()
                  if k not in ("frame_numbers","video_timestamps_us")} for p in parts],
    }

def main():
    parser=argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json",action="store_true")
    parser.add_argument("files",nargs="+",type=Path)
    args=parser.parse_args()
    for f in args.files:
        if not f.is_file():parser.error(f"File missing: {f}")
    summary=inspect(args.files)
    if args.json:
        print(json.dumps(summary,indent=2,ensure_ascii=False))
    else:
        print("QVFIL MLV 4K metadata / frame-number audit:",summary["result"])
        for label,key in (
            ("Files","files"),("RAWI dimensions","rawi_resolutions"),
            ("Nominal fps","declared_fps"),("VIDF blocks","observed_vidf_frames"),
            ("Missing frame numbers","missing_frame_numbers"),
            ("Repeated numbers","duplicated_frame_numbers"),
            ("Actual 4K width","is_true_4k_width"),
            ("Actual 3840x2160","is_true_uhd_3840x2160"),
        ):print(f"  {label}: {summary[key]}")
        for e in summary["errors"]:print("  ERROR:",e)
        print(summary["IMPORTANT"])
    raise SystemExit(0 if summary["result"]=="STRUCTURE_PASS" else 2)

if __name__=="__main__":
    main()
