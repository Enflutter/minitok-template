# CANONICAL AUTOGRADING TESTS — DO NOT EDIT.
# Tampering invalidates autograding (see README §Integrity) and is verified
# by grading/run_tests.py via SHA-256 checksums.
"""Part A1 — spec loading and validation (10 pts)."""

import json
import tempfile
import unittest
from pathlib import Path

from minitok.spec import SpecError, load_spec

VALID = {
    "tokens": [
        {"name": "WS", "regex": "( |\t)*", "skip": True},
        {"name": "INT", "regex": "<digit>*", "skip": False},
        {"name": "IDENT", "regex": "<letter>(<letter>|<digit>|_)*", "skip": False},
        {"name": "OP", "regex": "==|=|\\+|\\-", "skip": False},
    ]
}


def _write(obj) -> Path:
    f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump(obj, f)
    f.close()
    return Path(f.name)


class TestSpecLoading(unittest.TestCase):
    def test_load_valid_spec(self):
        spec = load_spec(_write(VALID))
        self.assertEqual(spec.names, ["WS", "INT", "IDENT", "OP"])
        self.assertTrue(spec.tokens[0].skip)
        self.assertFalse(spec.tokens[1].skip)

    def test_load_from_json_string(self):
        spec = load_spec(json.dumps(VALID))
        self.assertEqual(len(spec.tokens), 4)

    def test_preserves_order(self):
        spec = load_spec(json.dumps(VALID))
        self.assertEqual([t.name for t in spec.tokens],
                         ["WS", "INT", "IDENT", "OP"])

    def test_missing_file_raises(self):
        with self.assertRaises((OSError, SpecError)):
            load_spec("/nonexistent/path/spec.json")


class TestSpecValidation(unittest.TestCase):
    def test_malformed_json(self):
        with self.assertRaises(SpecError):
            load_spec("{not json")

    def test_empty_tokens_list(self):
        with self.assertRaises(SpecError):
            load_spec(json.dumps({"tokens": []}))

    def test_duplicate_names_rejected(self):
        bad = {"tokens": [
            {"name": "A", "regex": "a*", "skip": False},
            {"name": "A", "regex": "b*", "skip": False},
        ]}
        with self.assertRaises(SpecError):
            load_spec(json.dumps(bad))

    def test_empty_regex_rejected(self):
        bad = {"tokens": [{"name": "A", "regex": "", "skip": False}]}
        with self.assertRaises(SpecError):
            load_spec(json.dumps(bad))

    def test_unbalanced_parens_rejected(self):
        bad = {"tokens": [{"name": "A", "regex": "(a|b", "skip": False}]}
        with self.assertRaises(SpecError):
            load_spec(json.dumps(bad))

    def test_unknown_shorthand_rejected(self):
        bad = {"tokens": [{"name": "A", "regex": "<word>*", "skip": False}]}
        with self.assertRaises(SpecError):
            load_spec(json.dumps(bad))


if __name__ == "__main__":
    unittest.main()
