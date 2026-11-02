#!/usr/bin/env python3
"""QVFIL Media Engine 0.6.2: UI-only reliability/readiness interpretation.

Builds on user-tested v0.6.1 without modifying a single RAW recorder statement.
Flow from a real recording is bounded by source data production; it is NOT
maximum CF/SD sustained throughput. Compare writer I/O (itself approximate)
to theoretical source demand, plus actual stop cause and sample duration.
"""
import argparse
import subprocess
from pathlib import Path
import apply_media_engine_v061 as prior

UPSTREAM = prior.UPSTREAM
TARGET_FILE = prior.TARGET_FILE
replace_once = prior.replace_once

def patch(source):
    source = prior.patch(source)

    # Targeted rewrite of *only* the QVFIL menu warning. The recorder
    # remains bitwise identical to v0.6.1.
    before = '''    MENU_SET_NAME("QVFIL Media Engine");
    MENU_SET_VALUE("%s: %d.%d MiB/s",
        drive == 'A' ? "CF" : drive == 'B' ? "SD" : "?",
        needed / 10, needed % 10);
    if (!qvfilm_media_duration_ms || qvfilm_media_drive != drive)
    {
        MENU_SET_RINFO("NOT TESTED");
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "No capture-derived measurement on this target card yet. "
            "A short MLV recording can provide a preliminary estimate.");
        return;
    }
    MENU_SET_RINFO("Obs:%d.%d", (int)(qvfilm_media_stream_x10 / 10),
                   (int)(qvfilm_media_stream_x10 % 10));

    if (!qvfilm_media_stream_x10)
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "No useful write measurement. Review last MLV and stop reason.");
    else if ((uint64_t)qvfilm_media_stream_x10 * 100 < (uint64_t)needed * 120)
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "Observed %d.%d MiB/s < 120%% demand. Buffer risk. "
            "Use faster CF or lower RAW bandwidth.",
            (int)(qvfilm_media_stream_x10 / 10),
            (int)(qvfilm_media_stream_x10 % 10));
    else
        MENU_SET_WARNING(MENU_WARN_INFO,
            "Short capture only; no long-duration pass implied. "
            "Re-test 30s, 60s, then 3 minutes; inspect MLV frames.");'''

    after = '''    MENU_SET_NAME("QVFIL Media Engine");
    MENU_SET_VALUE("%s Need:%d.%d",
        drive == 'A' ? "CF" : drive == 'B' ? "SD" : "?",
        needed / 10, needed % 10);
    /* Flow during real-time capture is source-limited, NOT max card speed.
     * I/O is measured when FIO is active, so it is an imperfect capacity
     * proxy only (can overestimate real long-term throughput). */
    if (!qvfilm_media_duration_ms || qvfilm_media_drive != drive)
    {
        MENU_SET_RINFO("NO SAMPLE");
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "No MLV sample on this target since boot. Record a short CF test.");
        return;
    }

    MENU_SET_RINFO("I/O:%d.%d",
        (int)(qvfilm_media_writer_x10 / 10),
        (int)(qvfilm_media_writer_x10 % 10));

    if (qvfilm_last_stop_reason == 1)
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "BUFFER FULL on last capture. Lower RAW demand or use faster CF.");
    else if (qvfilm_last_stop_reason == 2)
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "FILE WRITE failed on last capture. Inspect CF/card/filesystem.");
    else if (!qvfilm_media_writer_x10 || !qvfilm_media_stream_x10)
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "No valid FIO speed sample; review Recording Report and MLV.");
    else if (qvfilm_media_duration_ms < 30000)
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "Short sample (<30s). No continuous-recording verdict. Retest.");
    else if ((uint64_t)qvfilm_media_writer_x10 * 100 <
             (uint64_t)needed * 120)
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "Estimated I/O headroom <20%%. Buffer risk; lower RAW or use CF.");
    else
        MENU_SET_WARNING(MENU_WARN_INFO,
            "Estimated headroom only. Verify MLV frames and a 3-min capture.");'''
    source = replace_once(source, before, after)

    source = replace_once(
        source,
        '    MENU_SET_NAME("QVFIL Recording Report");',
        '    MENU_SET_NAME("QVFIL Recording Report");'
        '\n    /* Flow is produced bytes/elapsed capture time, not card maximum. */'
    )
    source = replace_once(
        source,
        '        "Flow=total MB/s over wall time; I/O=active writer throughput. "'
        '\n        "These are estimates, not a card speed benchmark.",',
        '        "Flow=capture rate; I/O=FIO active rate. Not a card benchmark.",'
    )
    source = replace_once(
        source, 'MENU_SET_RINFO("QVFIL v0.6.1");',
        'MENU_SET_RINFO("QVFIL v0.6.2");'
    )
    source = replace_once(
        source,
        'v0.6.1: Canon menu formatter hotfix; recorder unchanged.',
        'v0.6.2: Reliability hints using writer I/O; recorder unchanged.'
    )
    return source


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--checkout", required=True)
    args = p.parse_args()
    root = Path(args.checkout).expanduser().resolve()
    if not (root / ".git").exists():
        p.error("Expected Magic Lantern git checkout")
    actual = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    if actual != UPSTREAM:
        p.error("Wrong source commit: " + actual)
    file = root / TARGET_FILE
    old = file.read_text(encoding="utf-8")
    new = patch(old)
    file.write_text(new, encoding="utf-8")
    print("QVFIL v0.6.2 UI-only reliability fix. RAW recorder unchanged.")
    print("EXPERIMENTAL: long-duration CF hardware test still required.")

if __name__ == "__main__":
    main()
