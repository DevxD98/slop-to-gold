#!/usr/bin/env python3
"""Accuracy tests for scripts/scan.py against fixtures with known counts.

Run: python3 tests/test_scan.py
"""
import os
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCAN = os.path.join(ROOT, "scripts", "scan.py")

FILES = {
    "src/a.ts": (
        "// header comment\n"
        "setTimeout(() => focus(), 0);\n"
        "requestAnimationFrame(draw);\n"
        "const x = y as any;\n"
        "// @ts-ignore\n"
        "try { go(); } catch (e) {}\n"
        "// TODO: remove\n"
    ),
    "src/b.tsx": (
        "useEffect(() => setFull(first + last), [first, last]);\n"
        "useEffect(() => {}, []);\n"
        "/* eslint-disable no-console */\n"
    ),
    "src/c.py": (
        "# a comment\n"
        "try:\n    go()\nexcept Exception:\n    pass\n"
        "x = 1  # noqa\n"
        "# HACK around the bug\n"
    ),
    # Must be ignored: skipped dirs and unknown extensions.
    "node_modules/lib/index.js": "setTimeout(a, 0); setTimeout(b, 0);\n",
    "dist/out.js": "setTimeout(a, 0);\n",
    ".claude/skills/x/s.py": "setTimeout(a, 0)\n",
    "notes.md": "setTimeout( TODO\n",
    # Byte-identical copy of a.ts: counted once.
    "copy/src/a.ts": None,
}

EXPECTED = {
    "timer-patch": 2,
    "useEffect": 2,
    "ts-escape": 2,
    "empty-catch": 2,
    "lint-disable": 2,
    "todo-hack": 2,
}


def run_scan(root, *args):
    return subprocess.run([sys.executable, SCAN, root, *args], capture_output=True, text=True, check=True).stdout


def totals(out):
    sect = out.split("pattern totals:")[1].split("top ")[0]
    return {k: int(v) for k, v in re.findall(r"^\s+(\S+)\s+(\d+)$", sect, re.M)}


class ScanAccuracy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = cls.tmp.name
        for rel, body in FILES.items():
            path = os.path.join(root, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(body if body is not None else FILES["src/a.ts"])
        cls.out = run_scan(root)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_pattern_counts_exact(self):
        self.assertEqual(totals(self.out), EXPECTED)

    def test_skips_vendor_and_build_dirs(self):
        self.assertNotIn("node_modules", self.out)
        self.assertNotIn("dist/", self.out)

    def test_dedups_identical_files(self):
        self.assertIn("skipped 1 byte-identical duplicate", self.out)

    def test_comment_ratio(self):
        # 6 comment lines out of 17 non-blank lines in a.ts, b.tsx, c.py
        m = re.search(r"comment ratio: (\d+)/(\d+)", self.out)
        self.assertEqual((int(m.group(1)), int(m.group(2))), (6, 17))

    def test_top_flag_limits_rows(self):
        out = run_scan(self.tmp.name, "--top", "1")
        rows = out.split("top 1 files by signal count:")[1].strip().splitlines()
        self.assertEqual(len(rows), 1)
        self.assertIn("a.ts", rows[0])

    def test_empty_repo(self):
        with tempfile.TemporaryDirectory() as d:
            out = run_scan(d)
            self.assertIn("comment ratio: 0/0", out)


if __name__ == "__main__":
    sys.exit(unittest.main(verbosity=2))
