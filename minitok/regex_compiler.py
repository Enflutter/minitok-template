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

from .automata import NFA


class RegexSyntaxError(ValueError):
    """Raised for malformed regular expressions."""


@dataclass
class _Node:
    """Suggested AST node. You may use your own representation."""

    kind: str  # 'literal' | 'class' | 'union' | 'concat' | 'plus'
    value: str = ""
    children: list["_Node"] | None = None


def parse(regex: str) -> _Node:
    """Parse a regex string into an AST. Raise RegexSyntaxError on bad input."""
    # TODO(PART A2): implement
    raise NotImplementedError("parse is not implemented yet (Part A2)")


def compile_regex(regex: str) -> NFA:
    """Compile a regex string to an NFA (see automata.NFA for the model).

    The returned NFA must accept exactly the (non-empty) language of the
    regex, have exactly one start state and one accept state, and use
    epsilon transitions as needed (automata.EPS).
    """
    # TODO(PART A2): implement
    raise NotImplementedError("compile_regex is not implemented yet (Part A2)")
