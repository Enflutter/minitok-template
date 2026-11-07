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
 
from dataclasses import dataclass
 
from .automata import NFA, EPS
 
GROUP_STAR_IS_KLEENE = True
 
 
class RegexSyntaxError(ValueError):
    """Raised for malformed regular expressions."""
 
 
@dataclass
class _Node:
    """AST node representation."""
 
    kind: str
    value: str = ""
    children: list["_Node"] | None = None
    grouped: bool = False 
 
 
def _lex(regex: str) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    i = 0
    n = len(regex)
    depth = 0
 
    while i < n:
        c = regex[i]
        if c == "\\":
            if i + 1 >= n:
                raise RegexSyntaxError("Trailing escape character in regex")
            tokens.append(("LITERAL", regex[i + 1]))
            i += 2
        elif c == "<":
            end = regex.find(">", i)
            content = regex[i + 1:end] if end != -1 else None
            if content is not None and content.isalpha():
                if content in ("letter", "digit"):
                    tokens.append(("CLASS", content))
                    i = end + 1
                else:
                    raise RegexSyntaxError(f"Unknown shorthand class: <{content}>")
            else:
                tokens.append(("LITERAL", "<"))
                i += 1
        elif c in ("|", "*", "(", ")"):
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth < 0:
                    raise RegexSyntaxError("Unbalanced parentheses in regex")
            tokens.append(("OP", c))
            i += 1
        else: 
            tokens.append(("LITERAL", c))
            i += 1
 
    if depth != 0:
        raise RegexSyntaxError("Unbalanced parentheses in regex")
    return tokens
 
 
def parse(regex: str) -> _Node:
    """Parse a regex string into an AST. Raise RegexSyntaxError on bad input."""
    if not isinstance(regex, str) or regex == "":
        raise RegexSyntaxError("Empty or invalid regex string")
 
    tokens = _lex(regex)
    pos = 0
 
    def peek():
        return tokens[pos] if pos < len(tokens) else None
 
    def advance():
        nonlocal pos
        t = tokens[pos]
        pos += 1
        return t
 
    def parse_union() -> _Node:
        node = parse_concat()
        while peek() == ("OP", "|"):
            advance()
            node = _Node("union", children=[node, parse_concat()])
        return node
 
    def parse_concat() -> _Node:
        t = peek()
        if t is None or t in (("OP", "|"), ("OP", ")")):
            raise RegexSyntaxError("Empty term or unexpected operator")
        node = parse_star()
        while True:
            t = peek()
            if t is None or t in (("OP", "|"), ("OP", ")")):
                break
            node = _Node("concat", children=[node, parse_star()])
        return node
 
    def parse_star() -> _Node:
        node = parse_atom()
        while peek() == ("OP", "*"):
            advance()
            if node.grouped and GROUP_STAR_IS_KLEENE:
                node = _Node("star", children=[node])
            else:
                node = _Node("plus", children=[node])
        return node
 
    def parse_atom() -> _Node:
        t = peek()
        if t is None:
            raise RegexSyntaxError("Unexpected end of regex")
        if t[0] == "LITERAL":
            advance()
            return _Node("literal", value=t[1])
        if t[0] == "CLASS":
            advance()
            return _Node("class", value=t[1])
        if t == ("OP", "("):
            advance()
            node = parse_union()
            if peek() != ("OP", ")"):
                raise RegexSyntaxError("Missing closing parenthesis")
            advance()
            node.grouped = True
            return node
        raise RegexSyntaxError(f"Unexpected token in regex: {t[1]!r}")
 
    ast = parse_union()
    if pos < len(tokens):
        raise RegexSyntaxError("Unexpected trailing tokens in regex")
    return ast
 
 
_LETTERS = [chr(c) for c in range(ord("a"), ord("z") + 1)] + [
    chr(c) for c in range(ord("A"), ord("Z") + 1)
]
_DIGITS = [str(d) for d in range(10)]
 
 
def compile_regex(regex: str) -> NFA:
    """Compile a regex string to an NFA (Thompson's construction).
 
    One start state, one accept state, epsilon transitions as needed.
    """
    ast = parse(regex)
 
    counter = 0
    trans: dict[int, dict[str, set[int]]] = {}
 
    def new_state() -> int:
        nonlocal counter
        counter += 1
        return counter - 1
 
    def add(src: int, sym: str, dst: int) -> None:
        trans.setdefault(src, {}).setdefault(sym, set()).add(dst)
 
    def build(node: _Node) -> tuple[int, int]:
        """Return (start, accept) of the fragment for this node."""
        if node.kind == "literal":
            s, a = new_state(), new_state()
            add(s, node.value, a)
            return s, a
 
        if node.kind == "class":
            s, a = new_state(), new_state()
            chars = _LETTERS if node.value == "letter" else _DIGITS
            for ch in chars:
                add(s, ch, a)
            return s, a
 
        if node.kind == "concat":
            s1, a1 = build(node.children[0])
            s2, a2 = build(node.children[1])
            add(a1, EPS, s2)
            return s1, a2
 
        if node.kind == "union":
            s, a = new_state(), new_state()
            s1, a1 = build(node.children[0])
            s2, a2 = build(node.children[1])
            add(s, EPS, s1)
            add(s, EPS, s2)
            add(a1, EPS, a)
            add(a2, EPS, a)
            return s, a
 
        if node.kind == "plus":
            s, a = new_state(), new_state()
            s1, a1 = build(node.children[0])
            add(s, EPS, s1)
            add(a1, EPS, s1) 
            add(a1, EPS, a)
            return s, a
 
        if node.kind == "star":
            s, a = new_state(), new_state()
            s1, a1 = build(node.children[0])
            add(s, EPS, s1)
            add(s, EPS, a) 
            add(a1, EPS, s1)
            add(a1, EPS, a)
            return s, a
 
        raise RegexSyntaxError(f"Unknown AST node kind: {node.kind}")
 
    start, accept = build(ast)
    alphabet = {sym for d in trans.values() for sym in d if sym != EPS}
 
    return NFA(
        states=set(range(counter)),
        alphabet=alphabet,
        transitions=trans,
        start=start,
        accepts={accept},
    )
 
