#!/usr/bin/env python3
"""QVFIL v0.6.7: one-shot, fail-closed 5D3.123 lossless diagnostic.

Layers on the hardware-accepted v0.6.6 patch and exact pinned ML 2025 source.
The 14-bit Lossless path remains blocked by default. The only exception is an
explicitly armed, one-shot, 25-frame probe at <=1280x720 / <=25fps on CF.
A failed compression frame is never marked SLOT_FULL or passed to the MLV
writer. The diagnostic is not a codec repair and is not hardware-certified.
"""
import argparse
import subprocess
from pathlib import Path
import apply_cinema_slim_v066 as prior

UPSTREAM = prior.UPSTREAM
TARGET_FILE = prior.TARGET_FILE
replace_once = prior.replace_once


def patch(source):
    source = prior.patch(source)

    # Volatile session-only state: no config persistence, no automatic arming.
    source = replace_once(
        source,
        'static volatile int qvfilm_last_stop_reason = 0; /* 0=none,1=buffer,2=write */',
        '''static volatile int qvfilm_last_stop_reason = 0; /* 0=none,1=buffer,2=write */

/* QVFIL v0.6.7 one-shot Lossless diagnostic. All state resets on module reload. */
#define QVFIL_LD_MAX_FRAMES 25
#define QVFIL_LD_IDLE 0
#define QVFIL_LD_ARMED 1
#define QVFIL_LD_RUNNING 2
#define QVFIL_LD_PASS 3
#define QVFIL_LD_FAIL 4
#define QVFIL_LD_INCOMPLETE 5
#define QVFIL_LD_DRAIN_TIMEOUT 6
#define QVFIL_LD_BLOCKED 7
#define QVFIL_LD_QUEUE_MISMATCH 8

static volatile int qvfilm_lossless_diag_armed = 0;
static volatile int qvfilm_lossless_diag_active = 0;
static volatile int qvfilm_lossless_diag_started = 0;
static volatile int qvfilm_lossless_diag_queue_started = 0;
static volatile int qvfilm_lossless_diag_drain_ack = 0;
static volatile int qvfilm_lossless_diag_fault = 0;
static volatile int qvfilm_lossless_diag_stop_requested = 0;
static volatile int qvfilm_lossless_diag_drain_timeout = 0;
static volatile int qvfilm_lossless_diag_reboot_required = 0;
static volatile int qvfilm_lossless_diag_status = QVFIL_LD_IDLE;
static volatile int qvfilm_lossless_diag_block_reason = 0;
static volatile int qvfilm_lossless_diag_error_code = 0;
static volatile int qvfilm_lossless_diag_error_frame = -1;
static volatile int qvfilm_lossless_diag_failed_slot = -1;
static volatile int qvfilm_lossless_diag_error_size = 0;
static volatile int qvfilm_lossless_diag_last_size = 0;
static volatile int qvfilm_lossless_diag_last_call_ms = 0;
static volatile int qvfilm_lossless_diag_ok_frames = 0;
static volatile int qvfilm_lossless_diag_width = 0;
static volatile int qvfilm_lossless_diag_height = 0;
static volatile int qvfilm_lossless_diag_fps = 0;
static volatile int qvfilm_lossless_diag_start_ms = 0;
static volatile int qvfilm_lossless_diag_elapsed_ms = 0;'''
    )

    # Shared preflight is checked both when the operator arms the test and
    # again when REC starts. It deliberately requires CF + a small mode.
    preflight = r"""
static int qvfilm_lossless_diag_preflight(void)
{
    if (!is_camera("5D3", "1.2.3")) return 1;
    if (!lv || !is_movie_mode() || !RAW_IS_IDLE) return 2;
    if (!raw_video_enabled) return 3;
    if (output_format != OUTPUT_14BIT_LOSSLESS) return 4;
    if (card_spanning || pre_record || rec_trigger || h264_proxy_menu) return 5;
    const char *dir = get_cf_dcim_dir();
    if (!dir || dir[0] != 'A' || !is_dir("A:/")) return 6;
    if (res_x <= 0 || res_y <= 0 || res_x > 1280 || res_y > 720) return 7;
    int fps1000 = fps_get_current_x1000();
    if (fps1000 <= 0 || fps1000 > 25000) return 8;
    if (qvfilm_lossless_diag_reboot_required) return 9;
    return 0;
}

static const char *qvfilm_lossless_diag_reason_text(int reason)
{
    switch (reason)
    {
        case 1: return "Requires Canon 5D3 firmware 1.2.3 / ML 5D3.123.";
        case 2: return "Enter Movie LiveView and stop any active recording.";
        case 3: return "Enable RAW video before arming the diagnostic.";
        case 4: return "Select exactly 14-bit Lossless as the data format.";
        case 5: return "Disable card spanning, pre-record, rec trigger and H.264 proxy.";
        case 6: return "Select the CF card (A:) as the recording destination.";
        case 7: return "Set a resolution from 640x360 up to 1280x720.";
        case 8: return "Set the frame rate to 25fps or lower.";
        case 9: return "Diagnostic drain was not confirmed. Reboot before RAW recording.";
        default: return "Preflight not ready. No diagnostic was armed.";
    }
}
"""
    source = replace_once(
        source,
        'void raw_video_rec_task()\n{\n'
        '    /* QVFIL guard: do not feed known-failing lossless to the encoder.\n'
        '     * This is a CONTAINMENT measure, not a repair of lossless compression.\n'
        '     * 14-bit uncompressed remains available for a fast enough card.\n'
        '     * Restrict to verified 5D3.123, leave other cameras unchanged. */\n'
        '    if (is_camera("5D3", "*") && OUTPUT_COMPRESSION)\n'
        '    {\n'
        '        printf("QVFIL: Lossless RAW blocked on 5D3.123 (known mlv_lite ASSERT).\\n");\n'
        '        NotifyBox(6000, "QVFIL: Lossless blocked. Use RAW uncompressed.");\n'
        '        return;\n'
        '    }\n'
        '    //~ console_show();',
        preflight + r'''
void raw_video_rec_task()
{
    /* A timed-out compressor may still own the buffers. Never start another
     * RAW session until a camera reboot clears this session-only latch.
     */
    if (qvfilm_lossless_diag_reboot_required)
    {
        NotifyBox(6000, "QVFIL: Reboot camera before any RAW recording.");
        return;
    }

    if (is_camera("5D3", "*") && OUTPUT_COMPRESSION)
    {
        int reason = qvfilm_lossless_diag_preflight();
        if (!qvfilm_lossless_diag_armed || reason)
        {
            qvfilm_lossless_diag_armed = 0;
            qvfilm_lossless_diag_status = QVFIL_LD_BLOCKED;
            qvfilm_lossless_diag_block_reason = reason ? reason : 4;
            printf("QVFIL: Lossless remains blocked; one-shot diagnostic not armed.\n");
            NotifyBox(6000, "QVFIL: Lossless blocked. Use 10-bit uncompressed or arm diagnostic.");
            return;
        }

        /* Consume the arm exactly once, before the recorder starts. */
        qvfilm_lossless_diag_armed = 0;
        qvfilm_lossless_diag_active = 1;
        qvfilm_lossless_diag_started = 1;
        qvfilm_lossless_diag_queue_started = 0;
        qvfilm_lossless_diag_drain_ack = 0;
        qvfilm_lossless_diag_fault = 0;
        qvfilm_lossless_diag_stop_requested = 0;
        qvfilm_lossless_diag_ok_frames = 0;
        qvfilm_lossless_diag_error_code = 0;
        qvfilm_lossless_diag_error_frame = -1;
        qvfilm_lossless_diag_failed_slot = -1;
        qvfilm_lossless_diag_error_size = 0;
        qvfilm_lossless_diag_last_size = 0;
        qvfilm_lossless_diag_last_call_ms = 0;
        qvfilm_lossless_diag_width = res_x;
        qvfilm_lossless_diag_height = res_y;
        qvfilm_lossless_diag_fps = (fps_get_current_x1000() + 500) / 1000;
        qvfilm_lossless_diag_start_ms = get_ms_clock();
        qvfilm_lossless_diag_elapsed_ms = 0;
        qvfilm_lossless_diag_status = QVFIL_LD_RUNNING;
        printf("QVFIL Lossless diagnostic armed: one-shot, max %d frames, %dx%d at %dfps.\n",
               QVFIL_LD_MAX_FRAMES, res_x, res_y, qvfilm_lossless_diag_fps);
    }
    else if (qvfilm_lossless_diag_armed)
    {
        /* The operator changed format after arming; do not leave a stale arm. */
        qvfilm_lossless_diag_armed = 0;
        qvfilm_lossless_diag_status = QVFIL_LD_BLOCKED;
        qvfilm_lossless_diag_block_reason = 4;
    }

    //~ console_show();'''
    )

    # Central failure handler: free the failed capture slot, latch the abort,
    # and stop future VSYNC capture. It never promotes an invalid frame to FULL.
    failure_helper = r"""
static void qvfilm_lossless_diag_mark_failure(int code, int frame, int slot, int output_size)
{
    qvfilm_lossless_diag_error_code = code;
    qvfilm_lossless_diag_error_frame = frame;
    qvfilm_lossless_diag_failed_slot = slot;
    qvfilm_lossless_diag_error_size = output_size;
    qvfilm_lossless_diag_status = QVFIL_LD_FAIL;
    qvfilm_lossless_diag_fault = 1;
    qvfilm_lossless_diag_active = 0;

    if (slot >= 0 && slot < COUNT(slots) &&
        slots[slot].status != SLOT_FREE &&
        slots[slot].status != SLOT_RESERVED)
    {
        free_slot(slot);
    }

    /* raw_rec_vsync_cbr() stops queueing new frames when buffer_full is set. */
    buffer_full = 1;
}
"""
    source = replace_once(
        source,
        'static void compress_task()\n{',
        failure_helper + '\nstatic void compress_task()\n{'
    )

    # INT_MIN is FIFO behind all outstanding frame messages. Acknowledge only
    # after the compression task has stopped its EDMAC spy and drained the queue.
    source = replace_once(
        source,
        '            edmac_stop_spy();\n\n            continue;',
        '            edmac_stop_spy();\n'
        '            if (qvfilm_lossless_diag_queue_started)\n'
        '                qvfilm_lossless_diag_drain_ack = 1;\n\n'
        '            continue;'
    )

    # After the first compression error, drop every later queued frame rather
    # than invoking the encoder again or allowing an incomplete slot to be saved.
    source = replace_once(
        source,
        '        int fullsize_index = msg >> 16;\n\n'
        '        /* we must receive a slot marked as "capturing in progress" */',
        '        int fullsize_index = msg >> 16;\n\n'
        '        if (qvfilm_lossless_diag_fault)\n'
        '        {\n'
        '            if (slot_index >= 0 && slot_index < COUNT(slots) &&\n'
        '                slots[slot_index].status != SLOT_FREE &&\n'
        '                slots[slot_index].status != SLOT_RESERVED)\n'
        '                free_slot(slot_index);\n'
        '            continue;\n'
        '        }\n\n'
        '        /* we must receive a slot marked as "capturing in progress" */'
    )

    # Capture elapsed time only for the diagnostic probe; no timing calls are
    # added to normal 10-bit/uncompressed recording.
    source = replace_once(
        source,
        '            int compressed_size = lossless_compress_raw_rectangle(\n'
        '                outSuite, fullSizeBuffer,\n'
        '                raw_info.width, (skip_x + 7) & ~7, skip_y & ~1,\n'
        '                res_x, res_y\n'
        '            );',
        '            uint32_t qvfilm_diag_t0 = qvfilm_lossless_diag_active ? get_ms_clock() : 0;\n'
        '            int compressed_size = lossless_compress_raw_rectangle(\n'
        '                outSuite, fullSizeBuffer,\n'
        '                raw_info.width, (skip_x + 7) & ~7, skip_y & ~1,\n'
        '                res_x, res_y\n'
        '            );\n'
        '            if (qvfilm_lossless_diag_active)\n'
        '                qvfilm_lossless_diag_last_call_ms = get_ms_clock() - qvfilm_diag_t0;'
    )

    # Intercept negative returns only in the explicitly armed diagnostic.
    # For all other cameras/builds, preserve the original upstream ASSERT.
    source = replace_once(
        source,
        '            if (compressed_size < 0 && !RAW_IS_IDLE)\n'
        '            {\n'
        '                printf("Compression error %d at frame %d\\n", compressed_size, frame_count-1);\n'
        '                ASSERT(0);\n'
        '            }\n\n'
        '            DeleteMemorySuite(outSuite);',
        '            if (compressed_size < 0 && qvfilm_lossless_diag_active)\n'
        '            {\n'
        '                printf("QVFIL LOSSLESS DIAG: code %d frame %d elapsed %dms\\n",\n'
        '                       compressed_size, frame_count-1, qvfilm_lossless_diag_last_call_ms);\n'
        '                DeleteMemorySuite(outSuite);\n'
        '                qvfilm_lossless_diag_mark_failure(compressed_size, frame_count-1, slot_index, 0);\n'
        '                continue;\n'
        '            }\n'
        '            if (compressed_size < 0 && !RAW_IS_IDLE)\n'
        '            {\n'
        '                printf("Compression error %d at frame %d\\n", compressed_size, frame_count-1);\n'
        '                ASSERT(0);\n'
        '            }\n\n'
        '            DeleteMemorySuite(outSuite);'
    )

    # Catch zero/oversize output before the original size assertions and before
    # shrink_slot()/frame_fake_edmac_check(). Never let a bad size reach MLV.
    source = replace_once(
        source,
        '            DeleteMemorySuite(outSuite);\n\n'
        '            if (1)\n            {\n'
        '                if (compressed_size >= frame_size_uncompressed)',
        '            DeleteMemorySuite(outSuite);\n\n'
        '            if (qvfilm_lossless_diag_active && compressed_size <= 0)\n'
        '            {\n'
        '                qvfilm_lossless_diag_mark_failure(-6, frame_count-1, slot_index, compressed_size);\n'
        '                continue;\n'
        '            }\n'
        '            if (qvfilm_lossless_diag_active && compressed_size >= frame_size_uncompressed)\n'
        '            {\n'
        '                qvfilm_lossless_diag_mark_failure(-4, frame_count-1, slot_index, compressed_size);\n'
        '                continue;\n'
        '            }\n'
        '            if (qvfilm_lossless_diag_active && compressed_size > max_frame_size - VIDF_HDR_SIZE - 4)\n'
        '            {\n'
        '                qvfilm_lossless_diag_mark_failure(-5, frame_count-1, slot_index, compressed_size);\n'
        '                continue;\n'
        '            }\n\n'
        '            if (1)\n            {\n'
        '                if (compressed_size >= frame_size_uncompressed)'
    )

    # Keep the last successful frame size and stop after 25 successful frames.
    # Any already-queued frames are still checked; a later error overrides PASS.
    source = replace_once(
        source,
        '            if (compressed_size > 0)\n'
        '            {\n'
        '                measured_compression_ratio = (compressed_size/128) * 100 / (frame_size_uncompressed/128);\n'
        '            }',
        '            if (compressed_size > 0)\n'
        '            {\n'
        '                measured_compression_ratio = (compressed_size/128) * 100 / (frame_size_uncompressed/128);\n'
        '                if (qvfilm_lossless_diag_active)\n'
        '                    qvfilm_lossless_diag_last_size = compressed_size;\n'
        '            }'
    )
    source = replace_once(
        source,
        '        /* mark it as completed */\n'
        '        slots[slot_index].status = SLOT_FULL;',
        '        /* mark it as completed */\n'
        '        slots[slot_index].status = SLOT_FULL;\n'
        '        if (qvfilm_lossless_diag_active && OUTPUT_COMPRESSION &&\n'
        '            !qvfilm_lossless_diag_stop_requested)\n'
        '        {\n'
        '            qvfilm_lossless_diag_ok_frames++;\n'
        '            if (qvfilm_lossless_diag_ok_frames >= QVFIL_LD_MAX_FRAMES)\n'
        '            {\n'
        '                qvfilm_lossless_diag_stop_requested = 1;\n'
        '                qvfilm_lossless_diag_status = QVFIL_LD_PASS;\n'
        '                printf("QVFIL LOSSLESS DIAG: %d frames passed; stopping one-shot probe.\\n",\n'
        '                       qvfilm_lossless_diag_ok_frames);\n'
        '                buffer_full = 1;\n'
        '            }\n'
        '        }'
    )

    # Mark the compression queue as started only after INT_MAX is posted.
    source = replace_once(
        source,
        '    msg_queue_post(compress_mq, INT_MAX);',
        '    msg_queue_post(compress_mq, INT_MAX);\n'
        '    if (qvfilm_lossless_diag_active)\n'
        '        qvfilm_lossless_diag_queue_started = 1;'
    )

    # Wait for the compressor task's FIFO drain acknowledgement before
    # truncating the writer queue or releasing any frame buffers.
    source = replace_once(
        source,
        '    msg_queue_post(compress_mq, INT_MIN);',
        r'''    msg_queue_post(compress_mq, INT_MIN);

    if (qvfilm_lossless_diag_queue_started)
    {
        uint32_t qvfilm_drain_t0 = get_ms_clock();
        while (!qvfilm_lossless_diag_drain_ack &&
               (uint32_t)(get_ms_clock() - qvfilm_drain_t0) < 5000)
        {
            msleep(10);
        }

        if (!qvfilm_lossless_diag_drain_ack)
        {
            /* The compressor may still own a frame buffer. Do not free it. */
            qvfilm_lossless_diag_drain_timeout = 1;
            qvfilm_lossless_diag_reboot_required = 1;
            qvfilm_lossless_diag_status = QVFIL_LD_DRAIN_TIMEOUT;
            qvfilm_lossless_diag_active = 0;
            printf("QVFIL LOSSLESS DIAG: queue drain timeout; buffers retained until reboot.\n");
        }
        else if (qvfilm_lossless_diag_fault)
        {
            /* Keep only the valid prefix before the failed slot. The failed
             * slot and all later queued frames are discarded, never written.
             */
            int qvfilm_tail_before = writing_queue_tail;
            int qvfilm_failed_pos = writing_queue_head;
            while (qvfilm_failed_pos != qvfilm_tail_before &&
                   writing_queue[qvfilm_failed_pos] != qvfilm_lossless_diag_failed_slot)
            {
                INC_MOD(qvfilm_failed_pos, COUNT(writing_queue));
            }

            if (qvfilm_failed_pos != qvfilm_tail_before)
            {
                int qvfilm_i = qvfilm_failed_pos;
                while (qvfilm_i != qvfilm_tail_before)
                {
                    int qvfilm_slot = writing_queue[qvfilm_i];
                    if (qvfilm_slot >= 0 && qvfilm_slot < COUNT(slots) &&
                        slots[qvfilm_slot].status != SLOT_FREE &&
                        slots[qvfilm_slot].status != SLOT_RESERVED)
                    {
                        free_slot(qvfilm_slot);
                    }
                    INC_MOD(qvfilm_i, COUNT(writing_queue));
                }
                writing_queue_tail = qvfilm_failed_pos;
            }
            else
            {
                /* Unexpected queue mismatch: discard every pending slot. */
                for (int qvfilm_i = writing_queue_head;
                     qvfilm_i != qvfilm_tail_before;
                     INC_MOD(qvfilm_i, COUNT(writing_queue)))
                {
                    int qvfilm_slot = writing_queue[qvfilm_i];
                    if (qvfilm_slot >= 0 && qvfilm_slot < COUNT(slots) &&
                        slots[qvfilm_slot].status != SLOT_FREE &&
                        slots[qvfilm_slot].status != SLOT_RESERVED)
                    {
                        free_slot(qvfilm_slot);
                    }
                }
                writing_queue_head = writing_queue_tail;
                qvfilm_lossless_diag_status = QVFIL_LD_QUEUE_MISMATCH;
                qvfilm_lossless_diag_reboot_required = 1;
            }
        }
    }'''
    )

    # If drain was not confirmed, skip queued frame writes; never free buffers
    # still potentially owned by the compression task.
    source = replace_once(
        source,
        '    /* write remaining frames */\n'
        '    /* H.264: we will be recording black frames during this time,',
        '    /* write remaining frames */\n'
        '    if (qvfilm_lossless_diag_drain_timeout)\n'
        '        writing_queue_head = writing_queue_tail;\n'
        '    /* H.264: we will be recording black frames during this time,'
    )

    # Preserve the original cleanup on normal/acknowledged stops. On a drain
    # timeout, retain frame buffers and require reboot to avoid use-after-free.
    source = replace_once(
        source,
        '    take_semaphore(settings_sem, 0);\n'
        '    free_buffers();\n'
        '    restore_bit_depth();\n'
        '    give_semaphore(settings_sem);',
        '    take_semaphore(settings_sem, 0);\n'
        '    if (!qvfilm_lossless_diag_drain_timeout)\n'
        '        free_buffers();\n'
        '    restore_bit_depth();\n'
        '    give_semaphore(settings_sem);'
    )

    # Close out the session report after the file is finalized.
    source = replace_once(
        source,
        'cleanup:\n'
        '    if (f) finish_chunk(f);',
        'cleanup:\n'
        '    if (f) finish_chunk(f);\n'
        '    if (qvfilm_lossless_diag_started)\n'
        '    {\n'
        '        qvfilm_lossless_diag_elapsed_ms = get_ms_clock() - qvfilm_lossless_diag_start_ms;\n'
        '        if (qvfilm_lossless_diag_status == QVFIL_LD_RUNNING)\n'
        '            qvfilm_lossless_diag_status = QVFIL_LD_INCOMPLETE;\n'
        '        qvfilm_lossless_diag_active = 0;\n'
        '        qvfilm_lossless_diag_started = 0;\n'
        '        qvfilm_lossless_diag_queue_started = 0;\n'
        '        if (qvfilm_lossless_diag_status == QVFIL_LD_PASS)\n'
        '            NotifyBox(5000, "QVFIL: 25-frame Lossless probe PASS. Check diagnostic MLV.");\n'
        '        else if (qvfilm_lossless_diag_status == QVFIL_LD_FAIL)\n'
        '            NotifyBox(6000, "QVFIL: Lossless probe stopped safely. Read diagnostic report.");\n'
        '        else if (qvfilm_lossless_diag_status == QVFIL_LD_DRAIN_TIMEOUT)\n'
        '            NotifyBox(7000, "QVFIL: Drain timeout. Reboot before any further RAW recording.");\n'
        '    }'
    )

    # The existing Shoot Check must distinguish the safe block from an armed
    # diagnostic. It remains read-only and never starts a disk benchmark.
    source = replace_once(
        source,
        '    if (is_camera("5D3", "*") && OUTPUT_COMPRESSION)\n'
        '    {\n'
        '        MENU_SET_RINFO("LJ BLOCKED");\n'
        '        MENU_SET_WARNING(MENU_WARN_NOT_WORKING,\n'
        '            "5D3 lossless is blocked due to prior ASSERT. "\n'
        '            "Use 10-bit uncompressed RAW.");\n'
        '        return;\n'
        '    }',
        '    if (is_camera("5D3", "*") && OUTPUT_COMPRESSION)\n'
        '    {\n'
        '        if (qvfilm_lossless_diag_armed)\n'
        '        {\n'
        '            MENU_SET_RINFO("DIAG ARMED");\n'
        '            MENU_SET_WARNING(MENU_WARN_ADVICE,\n'
        '                "One-shot only: <=1280x720, <=25fps, CF A:. Press REC once.");\n'
        '        }\n'
        '        else\n'
        '        {\n'
        '            MENU_SET_RINFO("LJ BLOCKED");\n'
        '            MENU_SET_WARNING(MENU_WARN_NOT_WORKING,\n'
        '                "Lossless remains blocked. Arm QVFIL Lossless Diagnostic for one controlled probe.");\n'
        '        }\n'
        '        return;\n'
        '    }'
    )

    # Update the Movie > Data format warning; do not imply that lossless is
    # repaired or generally available after the diagnostic build.
    source = replace_once(
        source,
        '    if (is_camera("5D3", "*") && OUTPUT_COMPRESSION)\n'
        '        MENU_SET_WARNING(MENU_WARN_NOT_WORKING,\n'
        '            "QVFIL: Lossless disabled on 5D3.123; choose RAW uncompressed.");',
        '    if (is_camera("5D3", "*") && OUTPUT_COMPRESSION)\n'
        '    {\n'
        '        if (qvfilm_lossless_diag_armed)\n'
        '            MENU_SET_WARNING(MENU_WARN_ADVICE,\n'
        '                "One-shot diagnostic armed. REC runs max 25 frames at <=720p/25 on CF.");\n'
        '        else\n'
        '            MENU_SET_WARNING(MENU_WARN_NOT_WORKING,\n'
        '                "Lossless blocked by QVFIL safety guard. Arm one-shot diagnostic only for testing.");\n'
        '    }'
    )

    # Explicit operator action and read-only report in the existing QVFIL menu.
    diag_menu = r"""
static MENU_SELECT_FUNC(qvfilm_lossless_diag_select)
{
    if (qvfilm_lossless_diag_armed)
    {
        qvfilm_lossless_diag_armed = 0;
        qvfilm_lossless_diag_status = QVFIL_LD_IDLE;
        NotifyBox(3000, "QVFIL: Lossless diagnostic disarmed.");
        return;
    }

    int reason = qvfilm_lossless_diag_preflight();
    if (reason)
    {
        qvfilm_lossless_diag_status = QVFIL_LD_BLOCKED;
        qvfilm_lossless_diag_block_reason = reason;
        NotifyBox(6000, qvfilm_lossless_diag_reason_text(reason));
        return;
    }

    qvfilm_lossless_diag_block_reason = 0;
    qvfilm_lossless_diag_armed = 1;
    qvfilm_lossless_diag_status = QVFIL_LD_ARMED;
    NotifyBox(5000, "QVFIL: One-shot armed. Press REC once; probe stops after 25 frames.");
}

static MENU_UPDATE_FUNC(qvfilm_lossless_diag_update)
{
    MENU_SET_NAME("QVFIL Lossless Diagnostic");
    MENU_SET_VALUE("%d/%d %dx%d %dfps",
                   qvfilm_lossless_diag_ok_frames, QVFIL_LD_MAX_FRAMES,
                   qvfilm_lossless_diag_width, qvfilm_lossless_diag_height,
                   qvfilm_lossless_diag_fps);

    if (qvfilm_lossless_diag_status == QVFIL_LD_ARMED)
    {
        MENU_SET_RINFO("ARMED");
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "One REC only. 14-bit Lossless, CF A:, <=1280x720 and <=25fps.");
    }
    else if (qvfilm_lossless_diag_status == QVFIL_LD_RUNNING)
    {
        MENU_SET_RINFO("RUNNING");
        MENU_SET_WARNING(MENU_WARN_INFO,
            "Probe is limited to 25 successful frames; do not power off while REC is active.");
    }
    else if (qvfilm_lossless_diag_status == QVFIL_LD_PASS)
    {
        MENU_SET_RINFO("PASS %d FR", qvfilm_lossless_diag_ok_frames);
        MENU_SET_WARNING(MENU_WARN_INFO,
            "Short probe only; not a sustained recording certification. Inspect the diagnostic MLV.");
    }
    else if (qvfilm_lossless_diag_status == QVFIL_LD_FAIL)
    {
        MENU_SET_RINFO("ERR %d F%d",
                       qvfilm_lossless_diag_error_code,
                       qvfilm_lossless_diag_error_frame);
        if (qvfilm_lossless_diag_error_code == -1)
            MENU_SET_WARNING(MENU_WARN_NOT_WORKING, "ERR -1: lossless encoder prerequisites not initialized.");
        else if (qvfilm_lossless_diag_error_code == -2)
            MENU_SET_WARNING(MENU_WARN_NOT_WORKING, "ERR -2: encoder completion callback timed out (1s).");
        else if (qvfilm_lossless_diag_error_code == -3)
            MENU_SET_WARNING(MENU_WARN_NOT_WORKING, "ERR -3: output lacks the expected JPEG Lossless signature.");
        else if (qvfilm_lossless_diag_error_code == -4)
            MENU_SET_WARNING(MENU_WARN_NOT_WORKING, "ERR -4: compressed frame size is not smaller than RAW input.");
        else if (qvfilm_lossless_diag_error_code == -5)
            MENU_SET_WARNING(MENU_WARN_NOT_WORKING, "ERR -5: compressed frame exceeds its allocated slot.");
        else
            MENU_SET_WARNING(MENU_WARN_NOT_WORKING, "ERR -6: compressor returned an empty frame.");
    }
    else if (qvfilm_lossless_diag_status == QVFIL_LD_DRAIN_TIMEOUT)
    {
        MENU_SET_RINFO("DRAIN TIMEOUT");
        MENU_SET_WARNING(MENU_WARN_NOT_WORKING,
            "Buffers retained. Reboot camera before any further RAW recording.");
    }
    else if (qvfilm_lossless_diag_status == QVFIL_LD_QUEUE_MISMATCH)
    {
        MENU_SET_RINFO("QUEUE ERROR");
        MENU_SET_WARNING(MENU_WARN_NOT_WORKING,
            "Unexpected writer queue state. Reboot camera before further RAW recording.");
    }
    else if (qvfilm_lossless_diag_status == QVFIL_LD_INCOMPLETE)
    {
        MENU_SET_RINFO("INCOMPLETE");
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            "REC stopped before 25 frames. Result is not a PASS; arm again only after reviewing settings.");
    }
    else if (qvfilm_lossless_diag_status == QVFIL_LD_BLOCKED)
    {
        MENU_SET_RINFO("BLOCKED");
        MENU_SET_WARNING(MENU_WARN_ADVICE,
            qvfilm_lossless_diag_reason_text(qvfilm_lossless_diag_block_reason));
    }
    else
    {
        int reason = qvfilm_lossless_diag_preflight();
        MENU_SET_RINFO(reason ? "NOT READY" : "READY");
        MENU_SET_WARNING(reason ? MENU_WARN_ADVICE : MENU_WARN_INFO,
            reason ? qvfilm_lossless_diag_reason_text(reason) :
            "SET arms one controlled 25-frame probe. 14-bit Lossless remains blocked otherwise.");
    }
}
"""
    source = replace_once(
        source,
        'static struct menu_entry qvfilm_hud_menu[] = {',
        diag_menu + '\nstatic struct menu_entry qvfilm_hud_menu[] = {'
    )
    source = replace_once(
        source,
        '    {\n'
        '        .name = "QVFIL Shoot Check",',
        '    {\n'
        '        .name = "QVFIL Lossless Diagnostic",\n'
        '        .select = qvfilm_lossless_diag_select,\n'
        '        .update = qvfilm_lossless_diag_update,\n'
        '        .icon_type = IT_ACTION,\n'
        '        .help = "Arms one fail-closed 14-bit Lossless diagnostic probe.",\n'
        '        .help2 = "CF only, <=1280x720, <=25fps, max 25 frames. Not for production.",\n'
        '    },\n'
        '    {\n'
        '        .name = "QVFIL Shoot Check",'
    )

    return source


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", required=True)
    args = parser.parse_args()
    root = Path(args.checkout).expanduser().resolve()
    if not (root / ".git").exists():
        parser.error("Expected exact Magic Lantern source Git checkout")
    actual = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    if actual != UPSTREAM:
        parser.error("Wrong Magic Lantern source commit %s; expected %s" % (actual, UPSTREAM))
    target = root / TARGET_FILE
    original = target.read_text(encoding="utf-8")
    updated = patch(original)  # strict anchors fail closed before writing
    target.write_text(updated, encoding="utf-8")
    print("QVFIL v0.6.7: one-shot fail-closed 14-bit Lossless diagnostic.")
    print("10-bit uncompressed path retained; default Lossless remains blocked.")
    print("EXPERIMENTAL REVIEW BUILD ONLY — NOT HARDWARE CERTIFIED / NOT FOR PRODUCTION.")


if __name__ == "__main__":
    main()
