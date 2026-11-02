#!/usr/bin/env python3
"""Offline static audit for the 5D3.123 lossless ASSERT; never runs on camera."""
import argparse
import unittest
from pathlib import Path

PARSER = argparse.ArgumentParser()
PARSER.add_argument("--mlv-lite", required=True)
PARSER.add_argument("--lossless", required=True)
PARSER.add_argument("--qvfilm-patch", required=True)
ARGS = PARSER.parse_args()

MLV = Path(ARGS.mlv_lite).read_text(encoding="utf-8")
LOSSLESS = Path(ARGS.lossless).read_text(encoding="utf-8")
PATCH = Path(ARGS.qvfilm_patch).read_text(encoding="utf-8")


def function_body(source, signature):
    start = source.index(signature)
    brace = source.index("{", start)
    depth = 0
    for i in range(brace, len(source)):
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
            if depth == 0:
                return source[brace + 1:i]
    raise AssertionError("Unclosed function: " + signature)


class LosslessAssertStaticAudit(unittest.TestCase):
    def test_assert_2742_is_negative_compression_guard(self):
        lines = MLV.splitlines()
        self.assertIn("if (compressed_size < 0 && !RAW_IS_IDLE)", MLV)
        self.assertIn('printf("Compression error %d at frame %d\\n", compressed_size, frame_count-1);', MLV)
        self.assertIn("ASSERT(0);", MLV)
        # Verify exact source line so future upstream changes fail closed.
        self.assertEqual(lines[2741].strip(), "ASSERT(0);")

    def test_compressor_negative_return_paths(self):
        body = function_body(LOSSLESS, "int lossless_compress_raw_rectangle(")
        self.assertIn("if (!TTL_ResLock || !lossless_sem || !TTL_Start)", body)
        self.assertIn("return -1;", body)
        self.assertIn("int err = take_semaphore(lossless_sem, 1000);", body)
        self.assertIn("if (err)", body)
        self.assertIn("return -2;", body)
        self.assertIn("MEM(WR1_Address) != 0xC4FFD8FF", body)
        self.assertIn("return -3;", body)
        self.assertIn("TTL_Prepare(TTL_ResLock, &TTL_Args);", body)
        self.assertIn("TTL_Start(&TTL_Args);", body)
        self.assertIn("TTL_Stop(&TTL_Args);", body)
        self.assertIn("TTL_Finish(TTL_ResLock, &TTL_Args, &output_size);", body)

    def test_qvfilm_guard_remains_fail_closed(self):
        guard = PATCH.index('if (is_camera("5D3", "*") && OUTPUT_COMPRESSION)')
        stop = PATCH.index('return;', guard)
        next_line = PATCH.index('    }', stop)
        self.assertLess(guard, stop)
        self.assertLess(stop, next_line)
        self.assertIn("Lossless RAW blocked on 5D3.123", PATCH)
        self.assertIn("This is a CONTAINMENT measure, not a repair", PATCH)
        self.assertNotIn("OUTPUT_COMPRESSION = 0", PATCH)

    def test_no_claim_that_error_code_is_known(self):
        # Existing ASSERT files omit the preceding printf; this test ensures
        # the source audit keeps all three distinct failure classes visible.
        body = function_body(LOSSLESS, "int lossless_compress_raw_rectangle(")
        for code in ("return -1;", "return -2;", "return -3;"):
            self.assertEqual(body.count(code), 1)


if __name__ == "__main__":
    unittest.main(argv=[__file__], verbosity=2)
