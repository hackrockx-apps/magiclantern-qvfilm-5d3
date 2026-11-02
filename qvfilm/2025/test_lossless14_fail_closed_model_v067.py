#!/usr/bin/env python3
"""Host-only model of the QVFIL v0.6.7 fail-closed queue contract.

This is a design regression test, not a simulator of Magic Lantern scheduling
and not proof that the camera C implementation is safe.
"""
from dataclasses import dataclass, field
import unittest


@dataclass
class Slot:
    frame: int
    state: str = "CAPTURING"


@dataclass
class Recorder:
    queue: list = field(default_factory=list)
    writer_frames: list = field(default_factory=list)
    error: dict | None = None
    stop_requested: bool = False
    finalized: bool = False

    def enqueue(self, frame):
        self.queue.append(Slot(frame))

    def compression_complete(self, slot, result, *, bpp=14, width=1920, height=1080):
        if result < 0:
            # Diagnostic is captured before any writer-eligible transition.
            self.error = {
                "code": result, "frame": slot.frame,
                "bpp": bpp, "width": width, "height": height,
            }
            self.stop_requested = True
            slot.state = "DISCARD"
            # A stop request invalidates pending slots too; none can reach writer.
            for pending in self.queue:
                if pending.state == "CAPTURING":
                    pending.state = "DISCARD"
            return "ABORT"
        slot.state = "FULL"
        return "READY"

    def writer_accept(self, slot):
        if slot.state != "FULL" or self.stop_requested:
            return False
        self.writer_frames.append(slot.frame)
        slot.state = "WRITTEN"
        return True

    def finalize_after_abort(self):
        if not self.stop_requested:
            raise RuntimeError("not aborting")
        if any(s.state in ("CAPTURING", "FULL") for s in self.queue):
            raise RuntimeError("queue not drained")
        self.finalized = True


class FailClosedContractTests(unittest.TestCase):
    def test_negative_codes_never_become_writer_eligible(self):
        for code in (-1, -2, -3):
            with self.subTest(code=code):
                rec = Recorder()
                failed = Slot(frame=41)
                rec.enqueue(failed)
                self.assertEqual(rec.compression_complete(failed, code), "ABORT")
                self.assertEqual(failed.state, "DISCARD")
                self.assertFalse(rec.writer_accept(failed))
                self.assertEqual(rec.writer_frames, [])
                self.assertEqual(rec.error["code"], code)
                self.assertEqual(rec.error["frame"], 41)

    def test_pending_frames_are_discarded_after_failure(self):
        rec = Recorder()
        failed = Slot(frame=12)
        pending = Slot(frame=13)
        rec.queue.extend([failed, pending])
        rec.compression_complete(failed, -2)
        self.assertEqual([s.state for s in rec.queue], ["DISCARD", "DISCARD"])
        self.assertFalse(rec.writer_accept(pending))
        rec.finalize_after_abort()
        self.assertTrue(rec.finalized)

    def test_successful_compression_remains_writer_eligible(self):
        rec = Recorder()
        good = Slot(frame=7)
        rec.enqueue(good)
        self.assertEqual(rec.compression_complete(good, 1843200), "READY")
        self.assertTrue(rec.writer_accept(good))
        self.assertEqual(rec.writer_frames, [7])

    def test_no_finalize_without_abort(self):
        rec = Recorder()
        with self.assertRaises(RuntimeError):
            rec.finalize_after_abort()


if __name__ == "__main__":
    unittest.main(verbosity=2)
