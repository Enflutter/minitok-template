# minitok — ITCS317 Course Project: Regular Languages Meet LLMs

> **Weight:** 5% of the course grade (100 pts + bonus) · **Released:** Week 6 (L17)
> **Repo link due:** Sunday of Week 6 · **Progress check:** Sunday of Week 10
> **Final due:** Week 13, day of L39, 23:59 (your pushed repo state is graded)
> **Work mode:** individually **or in pairs** (max 2 students — see §Working in pairs)

Modern LLMs don't read characters — they read **tokens**. Before any neural
network runs, a *tokenizer* segments raw text, and the classical core of every
tokenizer is exactly what you learn in ITCS317 Chapter 1: **regular
expressions compiled to finite automata, scanning by longest match.** In this
project you build that core yourself, then compare it against OpenAI's
production BPE tokenizer.

## How grading works (fork → push → autograde)

1. **Fork** this repository (keep it public so Actions can run).
2. **Clone your fork** and implement the `TODO`s in `minitok/`.
3. **Push.** GitHub Actions runs the canonical test suite on every push and
   posts your autograded score to the workflow-run summary (Actions tab).
4. **Submit your repo link on Blackboard** (Week 6, and confirm by Week 13).

| Part | What | Pts | Graded by |
|---|---|---|---|
| A1 | Token-spec loader + validation (`spec.py`) | 10 | CI (tests/test_spec.py) |
| A2 | Regex → NFA compiler (`regex_compiler.py`) | 20 | CI (tests/test_regex_compiler.py) |
| A3 | NFA → DFA with accept-priority (`automata.py`) | 20 | CI (tests/test_automata.py) |
| A4 | Maximal-munch scanner + CLI (`automata.py`, `__main__.py`) | 20 | CI (tests/test_tokenizer_cli.py) |
| B | LLM comparison using `tiktoken` + `report.pdf` | 30 | Manual |
| **Bonus** | **BPE from scratch** (`bpe_from_scratch.py`) | **+2% course total** | CI gate (tests/test_bpe_bonus.py) + report section |

The CI base score covers **A1–A4 (70 pts)**. Part B (the report) is graded by
the instructor from your repo. The bonus adds **2 percentage points to your
final course grade** (course total capped at 100%).

## Working in pairs

You may do this project individually or in a pair (max 2 students). If you
work as a pair:

- **One fork per pair** — work in the same repo; do not fork separately.
- **Both members submit the repo link** on Blackboard (Week 6 and Week 13).
- **Fill in [`CONTRIBUTIONS.md`](CONTRIBUTIONS.md)** at the repo root: names,
  student IDs, GitHub usernames, and each member's contributions.
- **Both members must appear in the commit history** with their own GitHub
  account. A repo where one member made all commits triggers a viva by default.
- Either member may be asked to explain **any** part of the code in a viva.
  If contributions are clearly unbalanced, individual scores may be adjusted.

## Part A — the tokenizer core (70 pts)

### A1. Token specification (`minitok/spec.py`, 10 pts)
A spec is JSON: an ordered list of token classes `{name, regex, skip}`.
`load_spec` validates it (see module docstring) and raises `SpecError` with a
helpful message on any violation. **Order matters**: it defines priority.

### A2. Regex → NFA (`minitok/regex_compiler.py`, 20 pts)
Support: literals (with `\` escapes for operator characters), the shorthand
classes `<letter>` and `<digit>`, union `|`, concatenation, grouping `( )`,
and postfix `*`. **In this spec, `*` means one-or-more** (a⁺): tokens must be
non-empty. Parse with precedence `* > concat > |`, then compile via
Thompson's construction (Sipser §1.3). `NFA.simulate` uses epsilon closures.

### A3. NFA → DFA (`minitok/automata.py`, 20 pts)
`eps_closure`, then `determinize` (subset construction, Sipser §1.2) that
labels each DFA accept state with a token-class name. When a DFA state
contains several labeled NFA accepts, keep the **highest-priority** label
(spec order). `build_token_dfa` combines all classes into one DFA.

### A4. Maximal-munch scanner + CLI (`minitok/automata.py`, `__main__.py`, 20 pts)
`scan` repeats: from the current position, run the DFA as far as possible,
remember the **last** accepted label/length, emit `(type, lexeme, position)`;
skip-classes are discarded; no match ⇒ `ScanError(position)`. CLI:

```
$ python -m minitok tokenize examples/tokens.json examples/sample.mini
IDENT	total	0
OP	=	6
FLOAT	3.14	8
...
```

## Part B — LLM comparison with `tiktoken` (30 pts, manual)

`tiktoken` (OpenAI) is the **only external library allowed**, and **only in
this part** (a separate script/notebook, e.g. `partb/compare.py`).

1. Pick a small corpus (≥ 2 KB): e.g., 20 lines of code + 2 paragraphs of prose.
2. Tokenize it with your Part-A tokenizer (using a spec of your design) and
   with `tiktoken.get_encoding("cl100k_base")`.
3. Write **`report.pdf`** (1–2 pages) comparing: vocabulary size; tokens per
   corpus; what happens to rare words, long identifiers, numbers, and emoji;
   and a short paragraph mapping theory to practice: *regular expressions ↔
   hand-written lexer-level tokens; BPE ↔ learned subword tokens; why both are
   "finite-state-flavored" but only one is a finite automaton.*

## Bonus — BPE from scratch (+2% course total)
Implement `train_bpe` / `encode` / `decode` in `minitok/bpe_from_scratch.py`
**using only the standard library**. All tests in `tests/test_bpe_bonus.py`
must pass in CI, **and** your `report.pdf` must include a section comparing
your scratch BPE's merges/output against `tiktoken` on the same corpus.
Partial bonus is not awarded; the gate is all-or-nothing.

## Constraints & integrity
- Parts A + bonus: **Python standard library only** (no `regex`, no automata
  packages, no `tiktoken`).
- Pairs: `CONTRIBUTIONS.md` must be completed and kept accurate; it is part of
  the grading evidence (see §Working in pairs).
- The files `tests/`, `grading/`, `.github/workflows/` are **canonical**: do
  not edit them. CI verifies their SHA-256 checksums on every run; modified
  canonical files fail the build and are treated as academic misconduct.
- AI assistants: allowed for boilerplate (CLI scaffolding, fixtures), for
  debugging specific error messages, and for prose polishing; **not** allowed
  to write the core algorithms (parser, Thompson's construction, subset
  construction, scanner, BPE). Disclose any use in this README ("Tools used").
  Undisclosed/out-of-bounds use = misconduct. You may be asked to explain any
  part of your code in a short viva.

## Milestones
| When | Requirement |
|---|---|
| Sun of Week 6 | Fork created; **repo link on Blackboard**; CI runs (even if red) |
| Sun of Week 10 | **Progress check**: CI green on A1–A2 suites; ungraded, but missing = **−5 pts** on the project; formative feedback follows |
| Week 13 (day of L39), 23:59 | Final state graded (last push before deadline) |

Late policy: 10% of the project's value per day, up to 3 days.

## Getting help
Office hours + TA hours weekly — bring a failing test name, not a general
question. Blackboard discussion board for spec clarifications (pinned answers).
