"""Part A2 — Regular-expression compiler: regex -> NFA (Thompson's construction).

Grammar you must support (see spec.py for the surface syntax):

    union   := concat ('|' concat)*
    concat  := star+
    star    := atom '*'*
    atom    := LITERAL | CLASS | '(' union ')'
    CLASS   := '<letter>' | '<digit>'
    LITERAL := alnum | escaped operator char | space | '_' | '.' etc.

Design guidance:
  - Parse to an AST (or postfix) with correct precedence (* > concat > |).
  - Compile each AST node to an NFA fragment following Sipser's inductive
    construction (§1.3): one start state, one accept state per fragment.
  - Remember: postfix '*' in THIS spec means "one or more" (a+), so
    `a*` compiles as concat(a, closure(a)). Empty matches must be impossible.
"""



from __future__ import annotations
 
from collections import deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING
 
if TYPE_CHECKING:
    from .spec import TokenSpec
 
EPS = "" 
 
 
class ScanError(ValueError):
    """Raised when no token class matches at the current input position.
 
    `position` is the 0-based character offset of the failure."""
 
    def __init__(self, message: str, position: int):
        super().__init__(message)
        self.position = position
 
 
@dataclass
class NFA:
    states: set[int] = field(default_factory=set)
    alphabet: set[str] = field(default_factory=set) 
    transitions: dict[int, dict[str, set[int]]] = field(default_factory=dict)
    start: int = 0
    accepts: set[int] = field(default_factory=set)
 
    def simulate(self, s: str) -> bool:
        """True iff this NFA accepts string s (on-the-fly subset simulation
        with epsilon closures). Handles epsilon cycles."""
        current = eps_closure(self, {self.start})
        for ch in s:
            moved: set[int] = set()
            for st in current:
                moved |= self.transitions.get(st, {}).get(ch, set())
            if not moved:
                return False
            current = eps_closure(self, moved)
        return bool(current & self.accepts)
 
 
@dataclass
class DFA:
    states: set[int] = field(default_factory=set)
    alphabet: set[str] = field(default_factory=set)
    transitions: dict[int, dict[str, int]] = field(default_factory=dict)
    start: int = 0
    accepts: dict[int, str] = field(default_factory=dict)
 
    def simulate(self, s: str) -> str | None:
        """Return the accepting label for s, or None if rejected/incomplete."""
        state = self.start
        for ch in s:
            nxt = self.transitions.get(state, {}).get(ch)
            if nxt is None:
                return None
            state = nxt
        return self.accepts.get(state)
 
 
@dataclass
class Token:
    type: str
    lexeme: str
    position: int 
    
 
def eps_closure(nfa: NFA, states: set[int]) -> set[int]:
    """Epsilon closure of a set of NFA states (iterative, cycle-safe)."""
    closure = set(states)
    stack = list(states)
    while stack:
        st = stack.pop()
        for nxt in nfa.transitions.get(st, {}).get(EPS, ()):
            if nxt not in closure:
                closure.add(nxt)
                stack.append(nxt)
    return closure
 
 
def determinize(nfa: NFA, label_of: dict[int, str], priority: list[str]) -> DFA:
    """Subset construction (Sipser §1.2) producing a tokenizer DFA.
 
    Choice: transitions to the dead (empty) state are omitted; DFA.simulate
    and scan treat a missing transition as rejection. DFA start state is 0.
    """
    rank = {name: i for i, name in enumerate(priority)}
    worst = len(priority)
 
    start_set = frozenset(eps_closure(nfa, {nfa.start}))
    ids: dict[frozenset, int] = {start_set: 0}
    transitions: dict[int, dict[str, int]] = {}
    accepts: dict[int, str] = {}
    queue = deque([start_set])
 
    while queue:
        current = queue.popleft()
        cid = ids[current]
 
        best_label = None
        best_rank = worst + 1
        for st in current:
            if st in label_of:
                name = label_of[st]
                r = rank.get(name, worst)
                if r < best_rank:
                    best_rank, best_label = r, name
        if best_label is not None:
            accepts[cid] = best_label
 
        moves: dict[str, set[int]] = {}
        for st in current:
            for sym, dsts in nfa.transitions.get(st, {}).items():
                if sym != EPS:
                    moves.setdefault(sym, set()).update(dsts)
 
        for sym, dsts in moves.items():
            target = frozenset(eps_closure(nfa, dsts))
            if target not in ids:
                ids[target] = len(ids)
                queue.append(target)
            transitions.setdefault(cid, {})[sym] = ids[target]
 
    return DFA(
        states=set(ids.values()),
        alphabet=set(nfa.alphabet),
        transitions=transitions,
        start=0,
        accepts=accepts,
    )
 
 
def build_token_dfa(spec: "TokenSpec") -> DFA:
    """Compile every token class of the spec into one combined DFA."""
    from .regex_compiler import compile_regex 
 
    transitions: dict[int, dict[str, set[int]]] = {}
    states: set[int] = set()
    alphabet: set[str] = set()
    label_of: dict[int, str] = {}
 
    new_start = 0
    offset = 1  
    states.add(new_start)
    transitions[new_start] = {EPS: set()}
 
    for tc in spec.tokens:
        nfa = compile_regex(tc.regex)
        for st in nfa.states:
            states.add(st + offset)
        for src, d in nfa.transitions.items():
            for sym, dsts in d.items():
                transitions.setdefault(src + offset, {}).setdefault(sym, set()).update(
                    d_ + offset for d_ in dsts
                )
        alphabet |= nfa.alphabet
        transitions[new_start][EPS].add(nfa.start + offset)
        for acc in nfa.accepts:
            label_of[acc + offset] = tc.name
        offset += max(nfa.states) + 1 if nfa.states else 1
 
    combined = NFA(
        states=states,
        alphabet=alphabet,
        transitions=transitions,
        start=new_start,
        accepts=set(label_of),
    )
    return determinize(combined, label_of, spec.names)
 
 
def scan(dfa: DFA, spec: "TokenSpec", text: str) -> list[Token]:
    """Tokenize `text` by repeated maximal munch from the DFA start state."""
    skip = {t.name for t in spec.tokens if t.skip}
    tokens: list[Token] = []
    n = len(text)
    pos = 0
 
    while pos < n:
        state = dfa.start
        last_label: str | None = None
        last_end = pos
        i = pos
 
        while i < n:
            nxt = dfa.transitions.get(state, {}).get(text[i])
            if nxt is None:
                break
            state = nxt
            i += 1
            if state in dfa.accepts:
                last_label = dfa.accepts[state]
                last_end = i
 
        if last_label is None:
            raise ScanError(
                f"Unexpected character {text[pos]!r} at position {pos}", pos
            )
 
        if last_label not in skip:
            tokens.append(Token(last_label, text[pos:last_end], pos))
        pos = last_end
 
    return tokens
