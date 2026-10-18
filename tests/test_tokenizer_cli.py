# CANONICAL AUTOGRADING TESTS — DO NOT EDIT.
# Tampering invalidates autograding (see README §Integrity) and is verified
# by grading/run_tests.py via SHA-256 checksums.
"""Part A4 — maximal-munch scanning + CLI (20 pts)."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from minitok.automata import ScanError, build_token_dfa, scan
from minitok.spec import load_spec

SPEC_JSON = """{
  "tokens": [
    {"name": "WS",    "regex": "( |\\t|\\n)*", "skip": true},
    {"name": "FLOAT", "regex": "<digit>*.<digit>*", "skip": false},
    {"name": "INT",   "regex": "<digit>*", "skip": false},
    {"name": "IDENT", "regex": "<letter>(<letter>|<digit>|_)*", "skip": false},
    {"name": "OP",    "regex": "==|=|\\+|\\-", "skip": false}
  ]
}"""


class ScanFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = load_spec(SPEC_JSON)
        cls.dfa = build_token_dfa(cls.spec)

    def tokens(self, text):
        return scan(self.dfa, self.spec, text)

    def types(self, text):
        return [t.type for t in self.tokens(text)]


class TestMaximalMunch(ScanFixture):
    def test_eq_vs_assign(self):
        # "==" must win over "=" by maximal munch
        toks = self.tokens("==")
        self.assertEqual([(t.type, t.lexeme) for t in toks], [("OP", "==")])

    def test_assignment(self):
        toks = self.tokens("=")
        self.assertEqual([(t.type, t.lexeme) for t in toks], [("OP", "=")])

    def test_float_beats_int_int(self):
        toks = self.tokens("3.14")
        self.assertEqual([(t.type, t.lexeme) for t in toks], [("FLOAT", "3.14")])

    def test_int_then_ident_is_error(self):
        with self.assertRaises(ScanError) as ctx:
            self.tokens("9lives")
        self.assertEqual(ctx.exception.position, 1)

    def test_positions_are_offsets(self):
        toks = self.tokens("ab 42")
        self.assertEqual(
            [(t.type, t.lexeme, t.position) for t in toks],
            [("IDENT", "ab", 0), ("INT", "42", 3)],
        )

    def test_whitespace_skipped(self):
        self.assertEqual(self.types(" \t\n"), [])

    def test_token_at_eof(self):
        toks = self.tokens("x=1 ")
        self.assertEqual(
            [(t.type, t.lexeme) for t in toks],
            [("IDENT", "x"), ("OP", "="), ("INT", "1")],
        )

    def test_error_position_after_skips(self):
        with self.assertRaises(ScanError) as ctx:
            self.tokens("x = @")
        self.assertEqual(ctx.exception.position, 4)


class TestCLI(ScanFixture):
    def _run(self, spec_text: str, src_text: str):
        with tempfile.TemporaryDirectory() as td:
            spec_p = Path(td, "tokens.json")
            src_p = Path(td, "in.mini")
            spec_p.write_text(spec_text, encoding="utf-8")
            src_p.write_text(src_text, encoding="utf-8")
            return subprocess.run(
                [sys.executable, "-m", "minitok", "tokenize",
                 str(spec_p), str(src_p)],
                capture_output=True, text=True, timeout=60,
            )

    def test_cli_success(self):
        r = self._run(SPEC_JSON, "total = 3.14 + x\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(
            r.stdout.strip().splitlines(),
            ["IDENT\ttotal\t0", "OP\t=\t6", "FLOAT\t3.14\t8",
             "OP\t+\t13", "IDENT\tx\t15"],
        )

    def test_cli_scan_error(self):
        r = self._run(SPEC_JSON, "ok @")
        self.assertEqual(r.returncode, 1)
        self.assertIn("position 3", r.stderr)


if __name__ == "__main__":
    unittest.main()
