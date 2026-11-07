r"""Part A1 — Token specification loader and validator.

A token specification is a JSON object:

{
  "tokens": [
    {"name": "WS",    "regex": "( |\t|\n)*",        "skip": true},
    {"name": "FLOAT", "regex": "<digit>*.<digit>*", "skip": false},
    {"name": "INT",   "regex": "<digit>*",          "skip": false},
    {"name": "IDENT", "regex": "<letter>(<letter>|<digit>|_)*", "skip": false},
    {"name": "OP",    "regex": "==|=|\+|-|\*|/|<|>", "skip": false}
  ]
}

Regex syntax (a small extension of Sipser §1.3):
  literals          letters, digits, and the operator characters + - * / < > =
                    when they are NOT acting as operators (use \\ to escape
                    operator chars: \\* means literal asterisk)
  <letter>          shorthand class: a-z A-Z
  <digit>           shorthand class: 0-9
  a|b               union
  ab                concatenation
  a*                Kleene star (in this spec: ONE or more repetitions, i.e.
                    the regular operation a(a)*  — "plus" — because a token
                    must be non-empty; see README §A2)
  ( ... )           grouping
  Precedence: * > concatenation > |

`skip: true` token classes (typically whitespace/comments) are recognized
and discarded by the scanner instead of being emitted.
"""
from __future__ import annotations
 
import json
from dataclasses import dataclass, field
from pathlib import Path
 
 
class SpecError(ValueError):
    """Raised when a token specification is invalid."""
 
 
@dataclass
class TokenClass:
    name: str
    regex: str
    skip: bool = False
 
 
@dataclass
class TokenSpec:
    tokens: list[TokenClass] = field(default_factory=list)
 
    @property
    def names(self) -> list[str]:
        return [t.name for t in self.tokens]
 

class ASTNode:
    pass
 
 
class Literal(ASTNode):
    def __init__(self, char: str):
        self.char = char
 
 
class Shorthand(ASTNode):
    def __init__(self, name: str):
        self.name = name
 
 
class Concat(ASTNode):
    def __init__(self, left: ASTNode, right: ASTNode):
        self.left = left
        self.right = right
 
 
class Union(ASTNode):
    def __init__(self, left: ASTNode, right: ASTNode):
        self.left = left
        self.right = right
 
 
class Star(ASTNode):
    """In this spec, '*' means one-or-more (plus)."""
 
    def __init__(self, expr: ASTNode):
        self.expr = expr
 
 
def tokenize_regex(regex_str: str) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    i = 0
    n = len(regex_str)
    paren_depth = 0
 
    while i < n:
        c = regex_str[i]
 
        if c == '\\':
            if i + 1 >= n:
                raise SpecError("Trailing escape character in regex")
            tokens.append(('LITERAL', regex_str[i + 1]))
            i += 2
 
        elif c == '<':

            end = regex_str.find('>', i)
            content = regex_str[i + 1:end] if end != -1 else None
            if content is not None and content.isalpha():
                if content in ('letter', 'digit'):
                    tokens.append(('SHORTHAND', content))
                    i = end + 1
                else:
                    raise SpecError(f"Unknown shorthand class: <{content}>")
            else:
                tokens.append(('LITERAL', '<'))
                i += 1
 
        elif c == '>':
            tokens.append(('LITERAL', '>'))
            i += 1
 
        elif c in ('|', '*', '(', ')'):
            if c == '(':
                paren_depth += 1
            
                if i + 1 < n and regex_str[i + 1] == ')':
                    raise SpecError("Empty parentheses () are not allowed")
            elif c == ')':
                paren_depth -= 1
                if paren_depth < 0:
                    raise SpecError("Unbalanced parentheses in regex")
            tokens.append(('OP', c))
            i += 1
 
        else:
            tokens.append(('LITERAL', c))
            i += 1
 
    if paren_depth != 0:
        raise SpecError("Unbalanced parentheses in regex")
 
    return tokens

 
def parse_tokens_to_ast(tokens: list[tuple[str, str]]) -> ASTNode:
    pos = 0
 
    def peek():
        return tokens[pos] if pos < len(tokens) else None
 
    def consume(expected_type=None, expected_val=None):
        nonlocal pos
        t = peek()
        if t is None:
            raise SpecError("Unexpected end of regex")
        if expected_type and t[0] != expected_type:
            raise SpecError(f"Expected token type {expected_type}, got {t[0]}")
        if expected_val and t[1] != expected_val:
            raise SpecError(f"Expected token value {expected_val}, got {t[1]}")
        pos += 1
        return t
 
    def parse_expr():
        node = parse_term()
        while peek() == ('OP', '|'):
            consume('OP', '|')
            right = parse_term()
            node = Union(node, right)
        return node
 
    def parse_term():
        t = peek()
        if t is None or t == ('OP', '|') or t == ('OP', ')'):
            raise SpecError("Empty term or unexpected operator")
 
        node = parse_factor()
        while True:
            nxt = peek()
            if nxt is None or nxt == ('OP', '|') or nxt == ('OP', ')'):
                break
            right = parse_factor()
            node = Concat(node, right)
        return node
 
    def parse_factor():
        node = parse_base()
        while peek() == ('OP', '*'):
            consume('OP', '*')
            node = Star(node)
        return node
 
    def parse_base():
        t = peek()
        if t is None:
            raise SpecError("Unexpected end of regex")
        if t[0] == 'LITERAL':
            consume()
            return Literal(t[1])
        if t[0] == 'SHORTHAND':
            consume()
            return Shorthand(t[1])
        if t == ('OP', '('):
            consume('OP', '(')
            node = parse_expr()
            consume('OP', ')')
            return node
        raise SpecError(f"Unexpected token in regex: {t}")
 
    node = parse_expr()
    if pos < len(tokens):
        raise SpecError(f"Extra tokens at end of regex starting at {tokens[pos]}")
    return node
 
 
def check_nullable(node: ASTNode) -> bool:
    """True if the regex can match the empty string."""
    if isinstance(node, (Literal, Shorthand)):
        return False
    if isinstance(node, Concat):
        return check_nullable(node.left) and check_nullable(node.right)
    if isinstance(node, Union):
        return check_nullable(node.left) or check_nullable(node.right)
    if isinstance(node, Star): 
        return check_nullable(node.expr)
    return False
 
 
def parse_and_validate_regex(regex_str: str) -> ASTNode:
    if not isinstance(regex_str, str) or regex_str == "":
        raise SpecError("Regex string cannot be empty")
    tokens = tokenize_regex(regex_str)
    ast = parse_tokens_to_ast(tokens)
    if check_nullable(ast):
        raise SpecError("Regex can match the empty string")
    return ast
 
def load_spec(source: str | Path) -> TokenSpec:
    """Load and validate a token specification from a JSON file path or a
    JSON string.
 
    Must raise SpecError (with a helpful message) for:
      - malformed JSON
      - missing/empty "tokens" list
      - duplicate token names
      - empty regex strings
      - regexes that can match the empty string (tokens must be non-empty)
      - unknown shorthand classes or unbalanced parentheses
 
    Returns a TokenSpec preserving the declared order (order defines
    priority for maximal-munch tie-breaking: earlier = higher priority).
    """
    if isinstance(source, Path):
        try:
            text = source.read_text(encoding="utf-8")
        except Exception as e:
            raise SpecError(f"Cannot read file {source}: {e}") from e
    else:
        try:
            is_file = Path(source).is_file()
        except (OSError, ValueError):
            is_file = False 
 
        if is_file:
            try:
                text = Path(source).read_text(encoding="utf-8")
            except Exception as e:
                raise SpecError(f"Cannot read file {source}: {e}") from e
        else:
            text = str(source)
 
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise SpecError(f"Malformed JSON: {e}") from e
 
    if not isinstance(data, dict):
        raise SpecError("JSON specification root must be an object")
 
    if "tokens" not in data:
        raise SpecError("Missing 'tokens' key in specification")
 
    tokens_list = data["tokens"]
    if not isinstance(tokens_list, list) or len(tokens_list) == 0:
        raise SpecError("'tokens' must be a non-empty list")
 
    token_classes: list[TokenClass] = []
    seen_names: set[str] = set()
 
    for item in tokens_list:
        if not isinstance(item, dict):
            raise SpecError("Token specification entry must be an object")
        if "name" not in item or "regex" not in item:
            raise SpecError("Token entry must have 'name' and 'regex' fields")
 
        name = item["name"]
        regex = item["regex"]
        skip = item.get("skip", False)
 
        if not isinstance(name, str) or not name.strip():
            raise SpecError("Token name must be a non-empty string")
        if not isinstance(regex, str):
            raise SpecError("Token regex must be a string")
        if not isinstance(skip, bool):
            raise SpecError("Token 'skip' must be a boolean")
 
        if name in seen_names:
            raise SpecError(f"Duplicate token name: '{name}'")
        seen_names.add(name)
 
        if regex == "":
            raise SpecError(f"Empty regex string for token '{name}'")
 
        try:
            parse_and_validate_regex(regex)
        except SpecError as e:
            raise SpecError(f"Token '{name}': {e}") from e
 
        token_classes.append(TokenClass(name=name, regex=regex, skip=skip))
 
    return TokenSpec(tokens=token_classes)
