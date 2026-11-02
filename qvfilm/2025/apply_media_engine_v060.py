#!/usr/bin/env python3
"""QVFIL Media Engine v0.6.0 on top of the exact 2025 + 0.5.6 patch.
Purely observational: no synthetic file benchmark, card overclock, or bypassing
the recorder's buffer/IO safety-stop paths.
"""
import argparse
import subprocess
from pathlib import Path
import apply_qvfilm_patch as prior

UPSTREAM = prior.UPSTREAM
TARGET_FILE = prior.TARGET_FILE
replace_once = prior.replace_once


def patch(source):
    source = prior.patch(source)
    source = replace_once(
        source,
        'static volatile int qvfilm_last_stop_reason = 0; /* 0=none,1=buffer,2=write */',
        '''static volatile int qvfilm_last_stop_reason = 0; /* 0=none,1=buffer,2=write */
static volatile char qvfilm_media_drive = '?';
static volatile unsigned int qvfilm_media_duration_ms = 0;
static volatile unsigned int qvfilm_media_stream_x10 = 0; /* MiB/s * 10; bytes written / wall time */
static volatile unsigned int qvfilm_media_writer_x10 = 0; /* MiB/s * 10; bytes / FIO time */
static volatile unsigned int qvfilm_media_end_queue = 0; /* MLV entries still queued at stop */
'''
    )

    # Local start timestamp only in RawRecTask. No added callbacks, bitmap
    # drawing or locks in the sensor capture path.
    source = replace_once(
        source,
        '    FILE* f = 0;\n    int last_block_size = 0; /* for detecting early stops */',
        '    FILE* f = 0;\n'
        '    uint32_t qvfilm_media_start_ms = 0;\n'
        '    int last_block_size = 0; /* for detecting early stops */'
    )
    source = replace_once(
        source,
        '    /* Need to start the recording of audio before the init of the mlv chunk */',
        '''    /* QVFIL measurement begins only after real MLV output file creation. */
    qvfilm_media_start_ms = get_ms_clock();
    qvfilm_media_drive = raw_movie_filename ? raw_movie_filename[0] : '?';
    qvfilm_media_duration_ms = 0;
    qvfilm_media_stream_x10 = 0;
    qvfilm_media_writer_x10 = 0;
    qvfilm_media_end_queue = 0;

    /* Need to start the recording of audio before the init of the mlv chunk */'''
    )

    # Snapshot before the original buffer flush. This is a passive estimate
    # from actual frames already written, not a storage bandwidth guarantee.
    # The stop reason set in v0.5.6 remains unchanged.
    source = replace_once(
        source,
        '    /* done, this will stop the vsync CBR and the copying task */\n'
        '    raw_recording_state = RAW_FINISHING;',
        '''    /* QVFIL capture-derived media metrics. No IO or bitmap work here.
     * Measured once at capture stop BEFORE buffer flushing begins.
     * A backlog indicates pending frames, not necessarily frame loss.
     */
    if (qvfilm_media_start_ms)
    {
        uint32_t elapsed = get_ms_clock() - qvfilm_media_start_ms;
        qvfilm_media_duration_ms = elapsed;
        if (elapsed && written_total > 0)
            qvfilm_media_stream_x10 =
                (unsigned int)((uint64_t)written_total * 10000ULL /
                ((uint64_t)elapsed * 1048576ULL));
        if (writing_time > 0 && written_total > 0)
            qvfilm_media_writer_x10 =
                (unsigned int)((uint64_t)written_total * 10000ULL /
                ((uint64_t)writing_time * 1048576ULL));
        qvfilm_media_end_queue =
            MOD(writing_queue_tail - writing_queue_head, COUNT(writing_queue));
    }

    /* done, this will stop the vsync CBR and the copying task */
    raw_recording_state = RAW_FINISHING;'''
    )

    menu = r"""
/* v0.6.0 Passive Media Engine.
 * Theoretical source pressure uses MiB/s so it is comparable to measured
 * FIO throughput. Numbers are short-session observations, not SD/CF specs.
 * No writes, automatic benchmark files, card frequency changes or dual-card
 * spanning. Buffer-full and IO failure behavior stays stock.
 */
static int qvfilm_media_demand_x10(void)
{
    int fps1000 = fps_get_current_x1000();
    if (res_x <= 0 || res_y <= 0 || BPP <= 0 || fps1000 <= 0)
        return 0;
    uint64_t bytes_per_second =
        (uint64_t)res_x * res_y * BPP * fps1000 / 8000;
    return (int)(bytes_per_second * 10 / 1048576ULL);
}

static MENU_UPDATE_FUNC(qvfilm_media_engine_update)
{
    const char *dir = get_cf_dcim_dir();
    char drive = dir ? dir[0] : '?';
    int needed = qvfilm_media_demand_x10();
    MENU_SET_VALUE("%c: %d.%d MiB/s", drive, needed / 10, needed % 10);
    if (!qvfilm_media_duration_ms || qvfilm_media_drive != drive)
    {
        MENU_SET_RINFO("NOT TESTED");
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "No capture-derived measurement on this target card yet. "
            "A short MLV recording can provide a preliminary estimate.");
        return;
    }
    MENU_SET_RINFO("Obs:%u.%u", qvfilm_media_stream_x10 / 10,
                   qvfilm_media_stream_x10 % 10);

    if (!qvfilm_media_stream_x10)
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "No useful write measurement. Review last MLV and stop reason.");
    else if ((uint64_t)qvfilm_media_stream_x10 * 100 < (uint64_t)needed * 120)
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "Observed %u.%u MiB/s < 120%% of demand. Buffer-stop risk. "
            "Use faster CF or lower RAW bandwidth.",
            qvfilm_media_stream_x10 / 10,
            qvfilm_media_stream_x10 % 10);
    else
        MENU_SET_WARNING(MENU_WARN_INFO,
            "Short capture only; no long-duration pass implied. "
            "Re-test 30s, 60s, then 3 minutes; inspect MLV frames.");
}

static MENU_UPDATE_FUNC(qvfilm_media_report_update)
{
    MENU_SET_VALUE("Flow:%u.%u", qvfilm_media_stream_x10 / 10,
                   qvfilm_media_stream_x10 % 10);
    MENU_SET_RINFO("I/O:%u.%u", qvfilm_media_writer_x10 / 10,
                   qvfilm_media_writer_x10 % 10);
    const char *stop =
        qvfilm_last_stop_reason == 1 ? "BUFFER" :
        qvfilm_last_stop_reason == 2 ? "WRITE" : "NONE";
    MENU_SET_WARNING(MENU_WARN_INFO,
        "Last MLV %c: capture %us, pending %u queue entries, stop %s. "
        "Flow=total MB/s over wall time; I/O=active writer throughput. "
        "These are estimates, not a card speed benchmark.",
        qvfilm_media_drive, qvfilm_media_duration_ms / 1000,
        qvfilm_media_end_queue, stop);
}
"""
    source = replace_once(
        source,
        'static struct menu_entry qvfilm_hud_menu[] = {',
        menu + '\nstatic struct menu_entry qvfilm_hud_menu[] = {'
    )
    source = replace_once(
        source,
        '''    {
        .name = "QVFIL Storage Check",
        .update = qvfilm_media_check_update,
        .help = "MLV target A=CF, B=SD. Shows estimated RAW bandwidth.",
        .help2 = "Last: BUFFER = queue full; WRITE = failed file write; NONE = no failure.",
    },
};''',
        '''    {
        .name = "QVFIL Storage Check",
        .update = qvfilm_media_check_update,
        .help = "MLV target A=CF, B=SD. Shows estimated RAW bandwidth.",
        .help2 = "Last: BUFFER = queue full; WRITE = failed file write; NONE = no failure.",
    },
    {
        .name = "QVFIL Media Engine",
        .update = qvfilm_media_engine_update,
        .help = "Read-only RAW bandwidth and headroom check; no speed overclock.",
        .help2 = "Capture-derived throughput is valid only for the last tested card.",
    },
    {
        .name = "QVFIL Recording Report",
        .update = qvfilm_media_report_update,
        .help = "Last actual MLV capture: stream, active writer, queue and stop.",
        .help2 = "Measured at end of capture before queued frames are flushed.",
    },
};'''
    )
    source = replace_once(source, 'MENU_SET_RINFO("QVFIL v0.5.6");',
                          'MENU_SET_RINFO("QVFIL v0.6.0");')
    source = replace_once(
        source,
        'v0.5.6: Low-flicker + read-only storage/stop diagnostics.',
        'v0.6.0: Passive CF/SD media profile; recorder safety preserved.'
    )
    return source


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", required=True)
    args = parser.parse_args()
    root = Path(args.checkout).expanduser().resolve()
    if not (root / ".git").exists():
        parser.error("Expected exact upstream git checkout.")
    commit = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    if commit != UPSTREAM:
        parser.error("Wrong upstream commit: " + commit)
    target = root / TARGET_FILE
    original = target.read_text(encoding="utf-8")
    patched = patch(original)  # validate all anchors before file mutation
    target.write_text(patched, encoding="utf-8")
    print("QVFIL v0.6.0 passive media profile applied, 5D3.123.")
    print("EXPERIMENTAL: CI pass is not camera-runtime evidence. No SD overclock.")


if __name__ == "__main__":
    main()
