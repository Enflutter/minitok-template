#!/usr/bin/env python3
"""ITCS317 minitok autograder.

Runs the canonical unittest suites, applies grading/weights.json, verifies
that the canonical test files have not been modified, and writes a score
summary (to $GITHUB_STEP_SUMMARY when running in CI, else stdout).

Exit code: 0 always (the score is data, not a build failure), except exit 3
if test-file integrity verification fails — that IS a CI failure.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEIGHTS = json.loads((ROOT / "grading" / "weights.json").read_text())
CHECKSUMS_FILE = ROOT / "grading" / "checksums.json"

CANONICAL_FILES = [
    "tests/test_spec.py",
    "tests/test_regex_compiler.py",
    "tests/test_automata.py",
    "tests/test_tokenizer_cli.py",
    "tests/test_bpe_bonus.py",
    "grading/weights.json",
    ".github/workflows/classroom.yml",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_integrity() -> list[str]:
    """Return a list of tampered files (empty if clean). No-op if the
    checksum manifest is absent (e.g., local dev runs)."""
    if not CHECKSUMS_FILE.exists():
        print("note: grading/checksums.json not found; skipping integrity check")
        return []
    expected = json.loads(CHECKSUMS_FILE.read_text())
    bad = []
    for rel, want in expected.items():
        p = ROOT / rel
        if not p.exists() or sha256(p) != want:
            bad.append(rel)
    return bad


def run_suite(test_file: str) -> dict[str, str]:
    """Run one test module; return {node_id: 'pass'|'fail'|'error'|'skip'}."""
    loader = unittest.TestLoader()
    suite = loader.discover(str(ROOT / "tests"), pattern=Path(test_file).name)
    stream = open(ROOT / "grading" / ".last_run.txt", "w")
    runner = unittest.TextTestRunner(stream=stream, verbosity=0)
    result = runner.run(suite)
    stream.close()

    out: dict[str, str] = {}

    def node_id(case) -> str:
        # 'tests.test_spec.TestSpecLoading.test_x' -> 'test_spec.TestSpecLoading.test_x'
        # Note: unittest._ErrorHolder (import/collection failures) has id()=None.
        raw = case.id() if callable(getattr(case, "id", None)) else None
        if raw is None:
            raw = str(case)  # e.g. "unittest.loader._FailedTest.test_spec"
        return raw.replace("tests.", "")

    for case, _tb in result.failures:
        out[node_id(case)] = "fail"
    for case, _tb in result.errors:
        out[node_id(case)] = "error"
    for case, _why in result.skipped:
        out[node_id(case)] = "skip"

    all_nodes = []
    stack = [suite]
    while stack:
        item = stack.pop()
        if isinstance(item, unittest.TestSuite):
            stack.extend(item)
        else:
            all_nodes.append(node_id(item))
    for n in all_nodes:
        out.setdefault(n, "pass")
    # Collection/import failures (e.g. student code raises at import time) put
    # pseudo-tests named '<module>' into the suite; mark real tests as error
    # so weights still resolve to 0 instead of false 'pass'.
    collection_failed = any(n.endswith("._FailedTest") or "_FailedTest" in n
                            for n in all_nodes)
    if collection_failed:
        for n in all_nodes:
            if not n.startswith("unittest"):
                out[n] = "error"
    return out


def main() -> int:
    tampered = verify_integrity()
    if tampered:
        msg = ("INTEGRITY FAILURE: canonical files modified: "
               + ", ".join(tampered))
        print(msg, file=sys.stderr)
        if (GITHUB_SUMMARY := __import__("os").environ.get("GITHUB_STEP_SUMMARY")):
            Path(GITHUB_SUMMARY).write_text(f"## ❌ {msg}\n")
        return 3

    # Allow `pip install tiktoken` to be absent locally without failing A-grading.
    subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0, '.')"],
                   cwd=ROOT, check=False)

    base_results: dict[str, str] = {}
    for tf in ["tests/test_spec.py", "tests/test_regex_compiler.py",
               "tests/test_automata.py", "tests/test_tokenizer_cli.py"]:
        base_results.update(run_suite(tf))
    bonus_results = run_suite("tests/test_bpe_bonus.py")

    earned = total = 0
    lines = ["| Test | Result | Points |", "|---|---|---|"]
    for node, pts in WEIGHTS["base"].items():
        status = base_results.get(node, "error")
        got = pts if status == "pass" else 0
        earned += got
        total += pts
        mark = {"pass": "✅", "fail": "❌", "error": "💥", "skip": "⏭️"}[status]
        lines.append(f"| `{node}` | {mark} {status} | {got}/{pts} |")

    bonus_nodes = WEIGHTS["bonus_tests"]
    bonus_passed = sum(1 for n in bonus_nodes if bonus_results.get(n) == "pass")
    bonus_ok = bonus_passed == len(bonus_nodes)

    lines += [
        "",
        f"## Base score (Parts A1–A4): **{earned} / {total}**",
        f"## Bonus tests (BPE from scratch): **{bonus_passed}/{len(bonus_nodes)} passed**"
        + (" — bonus CI gate: PASS ✅" if bonus_ok else " — bonus CI gate: not yet"),
        "",
        "Reminder: Part B (tiktoken report, 30 pts) is graded manually from this repo.",
        "Pairs: keep CONTRIBUTIONS.md up to date. The bonus also requires the Part B",
        "comparison section discussing your scratch BPE vs tiktoken (see README §Bonus).",
    ]
    summary = "\n".join(lines)
    print(summary)
    if (GITHUB_SUMMARY := __import__("os").environ.get("GITHUB_STEP_SUMMARY")):
        Path(GITHUB_SUMMARY).write_text("## ITCS317 minitok autograder\n\n" + summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
