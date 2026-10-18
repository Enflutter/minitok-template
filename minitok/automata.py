"""Parts A3/A4 — Finite automata models, determinization, and the scanner.

Data model (plain Python, no external deps):

  - An NFA is a set of states with transitions
        nfa.transitions[state][symbol] -> set of states
    symbol is a single character, or EPS (epsilon).
  - A DFA has a total transition function
        dfa.transitions[state][symbol] -> state
  - Accepting states of a tokenizer DFA are *labeled* with the token-class
    name they recognize (dfa.accepts[state] == "IDENT"), because one DFA
    serves the whole token specification.

The scanner performs MAXIMAL MUNCH (longest match wins) with PRIORITY
tie-breaking: among equally-long matches at the same position, the token
class declared earliest in the spec wins.
"""

from __future__ import annotations

from dataclasses import dataclass, field

EPS = ""  # epsilon-transition marker


class ScanError(ValueError):
    """Raised when no token class matches at the current input position.

    `position` is the 0-based character offset of the failure."""

    def __init__(self, message: str, position: int):
        super().__init__(message)
        self.position = position


@dataclass
class NFA:
    states: set[int] = field(default_factory=set)
    alphabet: set[str] = field(default_factory=set)  # excludes EPS
    transitions: dict[int, dict[str, set[int]]] = field(default_factory=dict)
    start: int = 0
    accepts: set[int] = field(default_factory=set)

    def simulate(self, s: str) -> bool:
        """True iff this NFA accepts string s (on-the-fly subset simulation
        with epsilon closures). Must handle epsilon cycles."""
        # TODO(PART A2/A3): implement
        raise NotImplementedError("NFA.simulate is not implemented yet")


@dataclass
class DFA:
    states: set[int] = field(default_factory=set)
    alphabet: set[str] = field(default_factory=set)
    transitions: dict[int, dict[str, int]] = field(default_factory=dict)
    start: int = 0
    # tokenizer DFAs label accepting states with token-class names:
    accepts: dict[int, str] = field(default_factory=dict)

    def simulate(self, s: str) -> str | None:
        """Return the accepting label for s, or None if rejected/incomplete."""
        # TODO(PART A3): implement
        raise NotImplementedError("DFA.simulate is not implemented yet")


@dataclass
class Token:
    type: str
    lexeme: str
    position: int  # 0-based offset of the first character of the lexeme


def eps_closure(nfa: NFA, states: set[int]) -> set[int]:
    """Epsilon closure of a set of NFA states."""
    # TODO(PART A2/A3): implement
    raise NotImplementedError("eps_closure is not implemented yet")


def determinize(nfa: NFA, label_of: dict[int, str], priority: list[str]) -> DFA:
    """Subset construction (Sipser §1.2) producing a tokenizer DFA.

    label_of: NFA accept state -> token-class name.
    priority: token-class names from highest to lowest priority; when a
    DFA state contains several labeled NFA accept states, keep the label
    with the highest priority (this implements tie-breaking).
    Transitions must be total over `nfa.alphabet` (use a dead state -1 or
    omit transitions to it consistently and document your choice).
    """
    # TODO(PART A3): implement
    raise NotImplementedError("determinize is not implemented yet")


def build_token_dfa(spec: "TokenSpec") -> DFA:
    """Compile every token class of the spec into one combined DFA.

    Steps: compile each class regex to an NFA (regex_compiler), union the
    NFAs with a new start state and epsilon edges, then determinize with
    per-class labels and spec-order priority.
    """
    # TODO(PART A3): implement
    raise NotImplementedError("build_token_dfa is not implemented yet")


def scan(dfa: DFA, spec: "TokenSpec", text: str) -> list[Token]:
    """Tokenize `text` by repeated maximal munch from the DFA start state.

    At each position: walk the DFA as far as possible, remember the last
    accepting label seen and its length; emit that Token (longest match);
    if the class has skip=true, discard instead. On no match, raise
    ScanError with the failing position. Must handle end-of-input while
    inside a token (e.g. text ending in an identifier).
    """
    # TODO(PART A4): implement
    raise NotImplementedError("scan is not implemented yet")
