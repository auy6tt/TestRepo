"""
Helper module used by the other scripts. You do not run it directly.

REDCap uses one small language for branching logic ("show the field only if..."),
calculated fields, @CALCTEXT and data quality rules. Examples:

    [smoke_status] = '1' or [smoke_status] = '2'
    [conditions(1)] = '1'                      (checkbox option 1 is ticked)
    round([weight_kg] / (([height_cm] / 100) ^ 2), 1)
    datediff([screening_arm_1][scr_date], [fu_date], "d")

This module can:
  parse(text)        turn the text into a small tree, or raise LogicError with a
                     plain-English message if the syntax is wrong
  references(tree)   list every [field] the logic uses
  evaluate(tree, ..) work out the value for one record (used by the cleaning
                     script and the fake-data generator)
  describe(tree, ..) write the logic out in plain English for the codebook

It only needs the Python standard library.
"""

from __future__ import annotations

import datetime as dt
import math
import re
import statistics
from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP, Decimal, InvalidOperation

# Smart variables that stand for a repeat instance, e.g. [field][current-instance]
INSTANCE_WORDS = {
    "current-instance", "previous-instance", "next-instance",
    "first-instance", "last-instance", "new-instance",
}

# REDCap functions we know about: name -> (minimum args, maximum args or None)
FUNCTIONS = {
    "if": (3, 3), "datediff": (3, 5), "round": (1, 2), "roundup": (1, 2),
    "rounddown": (1, 2), "sqrt": (1, 1), "abs": (1, 1), "min": (1, None),
    "max": (1, None), "mean": (1, None), "median": (1, None), "sum": (1, None),
    "stdev": (1, None), "log": (1, 2), "exp": (1, 1), "mod": (2, 2),
    "isnumber": (1, 1), "isinteger": (1, 1), "isblankormissingcode": (1, 1),
    "contains": (2, 2), "not_contain": (2, 2), "starts_with": (2, 2),
    "ends_with": (2, 2), "left": (2, 2), "right": (2, 2), "length": (1, 1),
    "find": (2, 2), "mid": (3, 3), "concat": (1, None), "concat_ws": (2, None),
    "upper": (1, 1), "lower": (1, 1), "trim": (1, 1), "year": (1, 1),
    "month": (1, 1), "day": (1, 1),
    # Used internally to check @CALCDATE([date], number, 'units')
    "calcdate": (3, 3),
}

COMPARISONS = {"=", "==", "<>", "!=", "<", "<=", ">", ">="}
CURLY_QUOTES = {"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', "\u2032": "'", "\u00b4": "'"}

_NUMBER = re.compile(r"\d+(?:\.\d*)?|\.\d+")
_WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_OPERATORS = ["<=", ">=", "<>", "!=", "==", "=", "<", ">", "+", "-", "*", "/", "^", "(", ")", ","]
_REF_HEAD = re.compile(r"([A-Za-z0-9_]+)(?:\(([^()]*)\))?")


class LogicError(Exception):
    """The logic text cannot be read. `message` is written for people."""

    def __init__(self, message: str, position: int | None = None):
        super().__init__(message)
        self.message = message
        self.position = position


class Unknown(Exception):
    """A value cannot be worked out (for example a smart variable such as [user-name])."""


@dataclass
class Ref:
    """One reference in square brackets, such as [age], [race(2)] or [visit_1_arm_1][sbp]."""

    text: str                     # the original text, e.g. "[visit_1_arm_1][sbp]"
    field: str | None             # variable name; None for smart variables
    code: str | None = None       # checkbox option code, e.g. "2" in [race(2)]
    event: str | None = None      # unique event name (or an event smart variable)
    instance: str | None = None   # repeat instance number or instance smart variable
    modifier: str | None = None   # e.g. "label" in [sex:label]
    smart: str | None = None      # smart variable name, e.g. "user-name"


@dataclass
class Token:
    kind: str      # num, str, ref, word, op, and, or, bool, eof
    value: object
    pos: int
    text: str


# ---------------------------------------------------------------------------
# Reading the text
# ---------------------------------------------------------------------------

def make_ref(parts: list[str], text: str, pos: int) -> Ref:
    """Build a Ref from the pieces of [a][b][c]."""
    if any(p.strip() == "" for p in parts):
        raise LogicError("empty square brackets [] - put a variable name inside", pos)
    if len(parts) > 3:
        raise LogicError(f"{text} has too many [...] parts in a row", pos)
    event = instance = None
    if len(parts) == 3:
        event, main, instance = parts
    elif len(parts) == 2:
        first, second = parts
        if second.strip().isdigit() or second.strip() in INSTANCE_WORDS:
            main, instance = first, second
        else:
            event, main = first, second
    else:
        main = parts[0]
    main = main.strip()
    head, _, modifier = main.partition(":")
    head = head.strip()
    if "-" in head:  # smart variables always contain a hyphen, e.g. [event-name]
        return Ref(text=text, field=None, smart=main, event=event, instance=instance)
    match = _REF_HEAD.fullmatch(head)
    if not match:
        raise LogicError(
            f"{text} is not a valid field reference (variable names use only "
            "letters, numbers and underscores)", pos)
    code = match.group(2)
    if code is not None:
        code = code.strip()
        if code == "":
            raise LogicError(f"{text} has empty brackets () - put the checkbox code inside, e.g. [race(2)]", pos)
    return Ref(text=text, field=match.group(1), code=code, event=event.strip() if event else None,
               instance=instance.strip() if instance else None, modifier=modifier.strip() or None)


def tokenize(text: str) -> list[Token]:
    tokens: list[Token] = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c.isspace():
            i += 1
            continue
        if c in CURLY_QUOTES:
            raise LogicError(
                f"curly quote {c} at character {i + 1} (usually pasted from Word). "
                "Retype it as a straight quote ' or \"", i)
        if c == "[":
            start, parts = i, []
            while i < n and text[i] == "[":
                close = text.find("]", i + 1)
                if close == -1:
                    raise LogicError(f"a '[' at character {i + 1} is never closed with ']'", i)
                inner = text[i + 1:close]
                if "[" in inner:
                    raise LogicError(f"a '[' at character {i + 1} is never closed with ']'", i)
                parts.append(inner)
                i = close + 1
            tokens.append(Token("ref", make_ref(parts, text[start:i], start), start, text[start:i]))
            continue
        if c == "]":
            raise LogicError(f"a ']' at character {i + 1} has no matching '['", i)
        if c in "'\"":
            close = text.find(c, i + 1)
            if close == -1:
                raise LogicError(f"a quote {c} at character {i + 1} is opened but never closed", i)
            tokens.append(Token("str", text[i + 1:close], i, text[i:close + 1]))
            i = close + 1
            continue
        match = _NUMBER.match(text, i)
        if match:
            tokens.append(Token("num", float(match.group()), i, match.group()))
            i = match.end()
            continue
        match = _WORD.match(text, i)
        if match:
            word = match.group()
            low = word.lower()
            if low in ("and", "or"):
                tokens.append(Token(low, low, i, word))
            elif low in ("true", "false"):
                tokens.append(Token("bool", low == "true", i, word))
            else:
                tokens.append(Token("word", word, i, word))
            i = match.end()
            continue
        if text.startswith("&&", i) or text.startswith("||", i):
            raise LogicError(f"'{text[i:i + 2]}' at character {i + 1}: REDCap uses the words 'and' / 'or'", i)
        for op in _OPERATORS:
            if text.startswith(op, i):
                tokens.append(Token("op", op, i, op))
                i += len(op)
                break
        else:
            raise LogicError(f"unexpected character '{c}' at character {i + 1}", i)
    tokens.append(Token("eof", None, n, ""))
    return tokens


class _Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.i = 0
        self.warnings: list[str] = []

    def peek(self) -> Token:
        return self.tokens[self.i]

    def take(self) -> Token:
        tok = self.tokens[self.i]
        self.i += 1
        return tok

    def is_op(self, *ops: str) -> bool:
        tok = self.peek()
        return tok.kind == "op" and tok.value in ops

    def parse(self):
        if self.peek().kind == "eof":
            raise LogicError("the logic is empty", 0)
        node = self.or_expr()
        tok = self.peek()
        if tok.kind != "eof":
            if tok.kind == "op" and tok.value == ")":
                raise LogicError(f"a ')' at character {tok.pos + 1} has no matching '('", tok.pos)
            raise LogicError(
                f"unexpected '{tok.text}' at character {tok.pos + 1} - is an 'and' / 'or' "
                "or an operator missing before it?", tok.pos)
        return node

    def or_expr(self):
        node = self.and_expr()
        while self.peek().kind == "or":
            self.take()
            node = ("or", node, self.and_expr())
        return node

    def and_expr(self):
        node = self.cmp_expr()
        while self.peek().kind == "and":
            self.take()
            node = ("and", node, self.cmp_expr())
        return node

    def cmp_expr(self):
        node = self.add_expr()
        if self.is_op(*COMPARISONS):
            tok = self.take()
            op = tok.value
            if op == "==":
                self.warnings.append("'==' used: REDCap's usual comparison is a single '='")
                op = "="
            if op == "!=":
                op = "<>"
            right = self.add_expr()
            node = ("cmp", op, node, right)
            if self.is_op(*COMPARISONS):
                nxt = self.peek()
                raise LogicError(
                    f"two comparisons in a row at character {nxt.pos + 1} (like 1 < [x] < 5). "
                    "Split them with 'and': [x] > 1 and [x] < 5", nxt.pos)
        return node

    def add_expr(self):
        node = self.mul_expr()
        while self.is_op("+", "-"):
            op = self.take().value
            node = ("bin", op, node, self.mul_expr())
        return node

    def mul_expr(self):
        node = self.pow_expr()
        while self.is_op("*", "/"):
            op = self.take().value
            node = ("bin", op, node, self.pow_expr())
        return node

    def pow_expr(self):
        node = self.unary()
        if self.is_op("^"):
            self.take()
            node = ("bin", "^", node, self.pow_expr())
        return node

    def unary(self):
        if self.is_op("-"):
            self.take()
            return ("neg", self.unary())
        if self.is_op("+"):
            self.take()
            return self.unary()
        return self.primary()

    def primary(self):
        tok = self.take()
        if tok.kind == "num":
            return ("num", tok.value, tok.text)
        if tok.kind == "str":
            return ("str", tok.value)
        if tok.kind == "bool":
            return ("bool", tok.value)
        if tok.kind == "ref":
            return ("ref", tok.value)
        if tok.kind == "word":
            if not self.is_op("("):
                raise LogicError(
                    f"unknown word '{tok.text}' at character {tok.pos + 1}. Text values need "
                    f"quotes (e.g. '{tok.text}') and variable names need square brackets "
                    f"(e.g. [{tok.text}])", tok.pos)
            self.take()  # (
            args = []
            if not self.is_op(")"):
                args.append(self.or_expr())
                while self.is_op(","):
                    self.take()
                    args.append(self.or_expr())
            if not self.is_op(")"):
                bad = self.peek()
                raise LogicError(
                    f"function {tok.text}( starting at character {tok.pos + 1} is not closed "
                    f"with ')' (found '{bad.text or 'the end'}' instead)", bad.pos)
            self.take()
            name = tok.text.lower()
            if name not in FUNCTIONS:
                self.warnings.append(f"'{tok.text}()' is not a REDCap function this checker knows - check the spelling")
            else:
                low, high = FUNCTIONS[name]
                if len(args) < low or (high is not None and len(args) > high):
                    expected = str(low) if low == high else f"{low} to {high if high else 'any number of'}"
                    raise LogicError(f"{tok.text}() needs {expected} values but has {len(args)}", tok.pos)
            return ("call", name, args)
        if tok.kind == "op" and tok.value == "(":
            node = self.or_expr()
            if not self.is_op(")"):
                bad = self.peek()
                raise LogicError(
                    f"a '(' at character {tok.pos + 1} is never closed with ')'", bad.pos)
            self.take()
            return node
        if tok.kind == "eof":
            raise LogicError("the logic ends too early - something is missing at the end", tok.pos)
        if tok.kind in ("and", "or"):
            raise LogicError(f"'{tok.text}' at character {tok.pos + 1} has nothing before it", tok.pos)
        raise LogicError(f"unexpected '{tok.text}' at character {tok.pos + 1}", tok.pos)


def parse(text: str):
    """Parse REDCap logic. Returns (tree, warnings). Raises LogicError."""
    parser = _Parser(tokenize(text))
    tree = parser.parse()
    return tree, parser.warnings


# ---------------------------------------------------------------------------
# Looking inside a parsed tree
# ---------------------------------------------------------------------------

def walk(node):
    """Yield every node in the tree."""
    yield node
    kind = node[0]
    if kind in ("and", "or"):
        yield from walk(node[1])
        yield from walk(node[2])
    elif kind in ("cmp", "bin"):
        yield from walk(node[2])
        yield from walk(node[3])
    elif kind == "neg":
        yield from walk(node[1])
    elif kind == "call":
        for arg in node[2]:
            yield from walk(arg)


def references(node) -> list[Ref]:
    return [n[1] for n in walk(node) if n[0] == "ref"]


def comparisons(node):
    """Yield (op, left, right) for every comparison in the tree."""
    for n in walk(node):
        if n[0] == "cmp":
            yield n[1], n[2], n[3]


def literal_text(node) -> str | None:
    """The text of a number or quoted string node, else None."""
    if node[0] == "str":
        return node[1]
    if node[0] == "num":
        return node[2]
    if node[0] == "neg" and node[1][0] == "num":
        return "-" + node[1][2]
    return None


def to_text(node) -> str:
    """Write a tree back out as REDCap logic."""
    kind = node[0]
    if kind == "num":
        return node[2]
    if kind == "str":
        return "'" + node[1] + "'" if "'" not in node[1] else '"' + node[1] + '"'
    if kind == "bool":
        return "true" if node[1] else "false"
    if kind == "ref":
        return node[1].text
    if kind == "neg":
        return "-" + to_text(node[1])
    if kind == "call":
        return node[1] + "(" + ", ".join(to_text(a) for a in node[2]) + ")"
    if kind == "bin":
        return f"{_wrap(node[2], node, False)} {node[1]} {_wrap(node[3], node, True)}"
    if kind == "cmp":
        return f"{_wrap(node[2], node, False)} {node[1]} {_wrap(node[3], node, True)}"
    if kind in ("and", "or"):
        return f"{_wrap(node[1], node, False)} {kind} {_wrap(node[2], node, True)}"
    return "?"


def _precedence(node) -> int:
    kind = node[0]
    if kind == "bin":
        return {"+": 4, "-": 4, "*": 5, "/": 5, "^": 6}[node[1]]
    return {"or": 1, "and": 2, "cmp": 3}.get(kind, 9)


def _wrap(child, parent, is_right: bool) -> str:
    text = to_text(child)
    mine, theirs = _precedence(child), _precedence(parent)
    needs = mine < theirs
    if mine == theirs and child[0] == "bin" and parent[0] == "bin":
        # a - (b - c), a / (b / c) and (a ^ b) ^ c keep their brackets
        needs = (is_right and parent[1] in "-/") or (not is_right and parent[1] == "^")
    return "(" + text + ")" if needs else text


# ---------------------------------------------------------------------------
# Plain-English description (for codebooks)
# ---------------------------------------------------------------------------

_OP_WORDS = {"=": "is", "<>": "is not", "<": "<", "<=": "<=", ">": ">", ">=": ">="}


def describe(node, fields: dict | None = None) -> str:
    """Plain-English version of logic. `fields` maps variable name -> object with
    .ftype and .choice_map (see redcap_dictionary.Field)."""
    fields = fields or {}
    kind = node[0]
    if kind in ("and", "or"):
        word = " AND " if kind == "and" else " OR "
        parts = []
        for child in (node[1], node[2]):
            text = describe(child, fields)
            if child[0] in ("and", "or") and child[0] != kind:
                text = "(" + text + ")"
            parts.append(text)
        return word.join(parts)
    if kind == "cmp":
        op, left, right = node[1], node[2], node[3]
        if left[0] != "ref" and right[0] == "ref":
            flip = {"<": ">", ">": "<", "<=": ">=", ">=": "<="}
            op, left, right = flip.get(op, op), right, left
        if left[0] == "ref":
            lit = literal_text(right)
            if lit is not None:
                return _describe_ref_compare(left[1], op, lit, fields)
        return f"{_plain(left)} {_OP_WORDS.get(op, op)} {_plain(right)}"
    return _plain(node)


def _plain(node) -> str:
    if node[0] == "ref":
        return _ref_name(node[1])
    return to_text(node)


def _ref_name(ref: Ref) -> str:
    if ref.smart:
        return f"[{ref.smart}]"
    name = ref.field
    if ref.event:
        name += f" (at event {ref.event})"
    if ref.instance:
        name += f" (instance {ref.instance})"
    return name


def _describe_ref_compare(ref: Ref, op: str, lit: str, fields: dict) -> str:
    field = fields.get(ref.field) if ref.field else None
    name = _ref_name(ref)
    if field is not None and ref.code is not None and getattr(field, "ftype", "") == "checkbox":
        option = field.choice_map.get(ref.code, ref.code)
        ticked = (op == "=" and lit == "1") or (op == "<>" and lit == "0")
        unticked = (op == "=" and lit == "0") or (op == "<>" and lit == "1")
        if ticked:
            return f'{name}: "{option}" is ticked'
        if unticked:
            return f'{name}: "{option}" is not ticked'
    if lit == "" and op in ("=", "<>"):
        return f"{name} is {'blank' if op == '=' else 'not blank'}"
    if field is not None and op in ("=", "<>") and getattr(field, "choice_map", None):
        label = field.choice_map.get(lit)
        if label is not None:
            return f'{name} {_OP_WORDS[op]} "{label}" ({lit})'
    shown = lit if _is_number(lit) else f"'{lit}'"
    return f"{name} {_OP_WORDS.get(op, op)} {shown}"


# ---------------------------------------------------------------------------
# Working out values (evaluation)
# ---------------------------------------------------------------------------

def _is_number(value) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return not math.isnan(value)
    if isinstance(value, str):
        try:
            float(value.strip())
            return value.strip() != ""
        except ValueError:
            return False
    return False


def _num(value):
    """Number, or None if blank / not a number."""
    if value is None:
        return None
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return None if math.isnan(value) else float(value)
    text = str(value).strip()
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _blank(value) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _truthy(value) -> bool:
    if isinstance(value, bool):
        return value
    if _blank(value):
        return False
    number = _num(value)
    if number is not None:
        return number != 0
    return str(value).lower() not in ("false", "")


def parse_datetime(value) -> dt.datetime | None:
    """Read a REDCap raw date / datetime (Y-M-D, as exported) or 'today' / 'now'."""
    if _blank(value):
        return None
    text = str(value).strip()
    low = text.lower()
    if low == "today":
        return dt.datetime.combine(_TODAY[0], dt.time())
    if low == "now":
        return dt.datetime.combine(_TODAY[0], dt.datetime.now().time())
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return dt.datetime.strptime(text, fmt)
        except ValueError:
            pass
    for fmt in ("%d-%m-%Y", "%m-%d-%Y"):  # literal dates written in other formats
        try:
            return dt.datetime.strptime(text, fmt)
        except ValueError:
            pass
    return None


_TODAY = [dt.date.today()]


def set_today(day: dt.date) -> None:
    """Fix the date used for 'today' (makes results repeatable)."""
    _TODAY[0] = day


def _round(value, places, mode):
    number = _num(value)
    if number is None:
        return None
    digits = int(_num(places) or 0)
    try:
        quant = Decimal(1).scaleb(-digits)
        return float(Decimal(repr(number)).quantize(quant, rounding=mode))
    except (InvalidOperation, ValueError):
        return None


def _compare(op, left, right) -> bool:
    if op in ("=", "<>"):
        if _blank(left) or _blank(right):
            same = _blank(left) and _blank(right)
        elif _is_number(left) and _is_number(right):
            same = _num(left) == _num(right)
        else:
            same = str(left) == str(right)
        return same if op == "=" else not same
    # <, <=, >, >= : a blank value never passes (as in REDCap)
    if _blank(left) or _blank(right):
        return False
    if _is_number(left) and _is_number(right):
        a, b = _num(left), _num(right)
    else:
        a, b = str(left), str(right)
    return {"<": a < b, "<=": a <= b, ">": a > b, ">=": a >= b}[op]


def evaluate(node, get_value):
    """Work out the value of a tree for one record.

    get_value(ref) must return the raw value of a reference as text ('' if blank),
    or raise Unknown if it cannot be worked out.
    Returns True/False for conditions, a float for numbers, text, or None for blank.
    """
    kind = node[0]
    if kind == "num":
        return node[1]
    if kind == "str":
        return node[1]
    if kind == "bool":
        return node[1]
    if kind == "ref":
        value = get_value(node[1])  # get_value raises Unknown for things it cannot look up
        return None if _blank(value) else value
    if kind == "neg":
        value = _num(evaluate(node[1], get_value))
        return None if value is None else -value
    if kind == "and":
        return _truthy(evaluate(node[1], get_value)) and _truthy(evaluate(node[2], get_value))
    if kind == "or":
        return _truthy(evaluate(node[1], get_value)) or _truthy(evaluate(node[2], get_value))
    if kind == "cmp":
        return _compare(node[1], evaluate(node[2], get_value), evaluate(node[3], get_value))
    if kind == "bin":
        a = _num(evaluate(node[2], get_value))
        b = _num(evaluate(node[3], get_value))
        if a is None or b is None:
            return None
        op = node[1]
        try:
            if op == "+":
                return a + b
            if op == "-":
                return a - b
            if op == "*":
                return a * b
            if op == "/":
                return None if b == 0 else a / b
            if op == "^":
                return float(a ** b)
        except (OverflowError, ZeroDivisionError, ValueError):
            return None
    if kind == "call":
        return _call(node[1], node[2], get_value)
    raise Unknown(f"cannot evaluate {kind}")


def _call(name, args, get_value):
    if name == "if":
        condition = evaluate(args[0], get_value)
        return evaluate(args[1] if _truthy(condition) else args[2], get_value)
    values = [evaluate(a, get_value) for a in args]
    if name in ("round", "roundup", "rounddown"):
        mode = {"round": ROUND_HALF_UP, "roundup": ROUND_CEILING, "rounddown": ROUND_FLOOR}[name]
        return _round(values[0], values[1] if len(values) > 1 else 0, mode)
    if name in ("sum", "mean", "median", "min", "max", "stdev"):
        numbers = [_num(v) for v in values if _num(v) is not None]  # blanks are ignored
        if not numbers:
            return None
        if name == "sum":
            return float(sum(numbers))
        if name == "mean":
            return statistics.fmean(numbers)
        if name == "median":
            return float(statistics.median(numbers))
        if name == "min":
            return min(numbers)
        if name == "max":
            return max(numbers)
        return statistics.stdev(numbers) if len(numbers) > 1 else None
    if name == "datediff":
        return _datediff(values)
    if name == "calcdate":
        start = parse_datetime(values[0])
        amount = _num(values[1])
        if start is None or amount is None:
            return None
        unit = str(values[2]).strip()
        seconds = {"y": 365.2425 * 86400, "M": 30.44 * 86400, "d": 86400, "h": 3600, "m": 60, "s": 1}.get(unit)
        if seconds is None:
            raise Unknown(f"unit '{unit}'")
        return (start + dt.timedelta(seconds=amount * seconds)).strftime("%Y-%m-%d")
    first = values[0] if values else None
    if name == "sqrt":
        number = _num(first)
        return None if number is None or number < 0 else math.sqrt(number)
    if name == "abs":
        number = _num(first)
        return None if number is None else abs(number)
    if name == "exp":
        number = _num(first)
        return None if number is None else math.exp(number)
    if name == "log":
        number = _num(first)
        if number is None or number <= 0:
            return None
        base = _num(values[1]) if len(values) > 1 else None
        return math.log(number, base) if base else math.log(number)
    if name == "mod":
        a, b = _num(values[0]), _num(values[1])
        return None if a is None or not b else math.fmod(a, b)
    if name == "isnumber":
        return _is_number(first)
    if name == "isinteger":
        if isinstance(first, str):
            return bool(re.fullmatch(r"-?\d+", first.strip()))
        number = _num(first)
        return number is not None and float(number).is_integer()
    if name == "isblankormissingcode":
        return _blank(first)
    text = "" if _blank(first) else str(first)
    if name in ("contains", "not_contain", "starts_with", "ends_with"):
        needle = "" if _blank(values[1]) else str(values[1])
        hay, sub = text.lower(), needle.lower()
        return {"contains": sub in hay, "not_contain": sub not in hay,
                "starts_with": hay.startswith(sub), "ends_with": hay.endswith(sub)}[name]
    if name == "length":
        return float(len(text))
    if name == "upper":
        return text.upper()
    if name == "lower":
        return text.lower()
    if name == "trim":
        return text.strip()
    if name in ("left", "right"):
        count = int(_num(values[1]) or 0)
        return text[:count] if name == "left" else (text[-count:] if count else "")
    if name == "mid":
        start, count = int(_num(values[1]) or 1), int(_num(values[2]) or 0)
        return text[start - 1:start - 1 + count]
    if name == "find":
        needle = "" if _blank(values[1]) else str(values[1])
        return float(text.lower().find(needle.lower()) + 1)
    if name == "concat":
        return "".join("" if _blank(v) else _fmt(v) for v in values)
    if name == "concat_ws":
        sep = "" if _blank(values[0]) else str(values[0])
        return sep.join(_fmt(v) for v in values[1:] if not _blank(v))
    if name in ("year", "month", "day"):
        when = parse_datetime(first)
        if when is None:
            return None
        return float(getattr(when, name))
    raise Unknown(f"function {name}()")


def _fmt(value) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _datediff(values):
    first, second, unit = values[0], values[1], values[2]
    rest = values[3:]
    signed = False
    for extra in rest:  # optional old-style date format ("ymd") and/or signed flag
        if isinstance(extra, bool):
            signed = extra
        elif isinstance(extra, str) and extra.lower() in ("true", "false"):
            signed = extra.lower() == "true"
    start, end = parse_datetime(first), parse_datetime(second)
    if start is None or end is None:
        return None
    seconds = (end - start).total_seconds()
    unit = str(unit).strip()
    per = {"y": 365.2425 * 86400, "M": 30.44 * 86400, "d": 86400, "h": 3600, "m": 60, "s": 1}.get(unit)
    if per is None:
        raise Unknown(f"datediff unit '{unit}'")
    result = seconds / per
    return result if signed else abs(result)


def format_number(value) -> str:
    """Format a calculated value the way REDCap stores it (no trailing .0)."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return ""
        if value.is_integer():
            return str(int(value))
        return repr(round(value, 10)).rstrip("0").rstrip(".")
    return str(value)


# Public names for the helpers other scripts use
truthy = _truthy
is_number = _is_number
to_number = _num
