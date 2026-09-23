"""Synthex — constructed language for abilities, parameters, and units.

Grammar (EBNF):
    program     = statement*
    statement   = ability_decl | param_decl | unit_decl | alter_stmt | import_stmt
    ability_decl = 'ability' IDENT '{' ability_body '}'
    param_decl  = 'param' IDENT '{' param_body '}'
    unit_decl   = 'unit' IDENT '{' unit_body '}'
    alter_stmt  = 'alter' IDENT '->' IDENT '{' alter_body '}'
    import_stmt = 'import' STRING

    ability_body = (ability_field ';')*
    param_body  = (param_field ';')*
    unit_body   = (unit_field ';')*
    alter_body  = (alter_field ';')*

    ability_field = 'category' ':' STRING
                  | 'desc' ':' STRING
                  | 'desc_ru' ':' STRING
                  | 'params' ':' '[' IDENT_list ']'

    param_field  = 'type' ':' STRING
                 | 'physical' ':' STRING
                 | 'default' ':' NUMBER
                 | 'range' ':' '[' NUMBER ',' NUMBER ']'
                 | 'unit' ':' IDENT
                 | 'formula' ':' STRING

    unit_field   = 'symbol' ':' STRING
                 | 'base' ':' IDENT
                 | 'factor' ':' NUMBER
                 | 'offset' ':' NUMBER

    alter_field  = 'param' ':' IDENT
                 | 'op' ':' ('set' | 'add' | 'mul' | 'clamp')
                 | 'value' ':' NUMBER
                 | 'min' ':' NUMBER
                 | 'max' ':' NUMBER

    IDENT      = letter (letter | digit | '-' | '_')*
    STRING     = '"' <any chars> '"'
    NUMBER     = digit+ ('.' digit+)?
    IDENT_list = IDENT (',' IDENT)*
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

# ---------------------------------------------------------------------------
# Token types
# ---------------------------------------------------------------------------


class TT(Enum):
    """Token type."""

    # Literals
    IDENT = auto()
    STRING = auto()
    NUMBER = auto()

    # Keywords
    ABILITY = auto()
    PARAM = auto()
    UNIT = auto()
    ALTER = auto()
    IMPORT = auto()

    # Field keywords
    CATEGORY = auto()
    DESC = auto()
    DESC_RU = auto()
    PARAMS = auto()
    TYPE = auto()
    PHYSICAL = auto()
    DEFAULT = auto()
    RANGE = auto()
    FORMULA = auto()
    SYMBOL = auto()
    BASE = auto()
    FACTOR = auto()
    OFFSET = auto()
    OP = auto()
    VALUE = auto()
    MIN = auto()
    MAX = auto()

    # Operators
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COLON = auto()
    SEMICOLON = auto()
    COMMA = auto()
    ARROW = auto()

    # Special
    EOF = auto()
    NEWLINE = auto()


KEYWORDS: dict[str, TT] = {
    "ability": TT.ABILITY,
    "param": TT.PARAM,
    "unit": TT.UNIT,
    "alter": TT.ALTER,
    "import": TT.IMPORT,
    "category": TT.CATEGORY,
    "desc": TT.DESC,
    "desc_ru": TT.DESC_RU,
    "params": TT.PARAMS,
    "type": TT.TYPE,
    "physical": TT.PHYSICAL,
    "default": TT.DEFAULT,
    "range": TT.RANGE,
    "formula": TT.FORMULA,
    "symbol": TT.SYMBOL,
    "base": TT.BASE,
    "factor": TT.FACTOR,
    "offset": TT.OFFSET,
    "op": TT.OP,
    "value": TT.VALUE,
    "min": TT.MIN,
    "max": TT.MAX,
}


# ---------------------------------------------------------------------------
# Token
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Token:
    type: TT
    value: str | float
    line: int
    col: int


# ---------------------------------------------------------------------------
# Lexer
# ---------------------------------------------------------------------------


class Lexer:
    """Tokenize Synthex source."""

    def __init__(self, source: str) -> None:
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: list[Token] = []

    def tokenize(self) -> list[Token]:
        while self.pos < len(self.source):
            ch = self.source[self.pos]

            if ch == "\n":
                self.tokens.append(Token(TT.NEWLINE, "\\n", self.line, self.col))
                self.pos += 1
                self.line += 1
                self.col = 1
            elif ch.isspace():
                self.pos += 1
                self.col += 1
            elif ch == "#":
                self._skip_comment()
            elif ch == '"':
                self._read_string()
            elif ch in "{}[]:,;->":
                self._read_punct(ch)
            elif ch.isdigit() or (
                ch == "."
                and self.pos + 1 < len(self.source)
                and self.source[self.pos + 1].isdigit()
            ):
                self._read_number()
            elif ch.isalpha() or ch == "_":
                self._read_ident()
            else:
                raise SyntaxError(
                    f"Unexpected character '{ch}' at {self.line}:{self.col}"
                )

        self.tokens.append(Token(TT.EOF, "", self.line, self.col))
        return self.tokens

    def _skip_comment(self) -> None:
        while self.pos < len(self.source) and self.source[self.pos] != "\n":
            self.pos += 1
            self.col += 1

    def _read_string(self) -> None:
        start_col = self.col
        self.pos += 1  # skip opening quote
        self.col += 1
        buf: list[str] = []
        while self.pos < len(self.source) and self.source[self.pos] != '"':
            if self.source[self.pos] == "\\":
                self.pos += 1
                self.col += 1
                if self.pos < len(self.source):
                    buf.append(self.source[self.pos])
            else:
                buf.append(self.source[self.pos])
            self.pos += 1
            self.col += 1
        if self.pos >= len(self.source):
            raise SyntaxError(f"Unterminated string at {self.line}:{start_col}")
        self.pos += 1  # skip closing quote
        self.col += 1
        self.tokens.append(Token(TT.STRING, "".join(buf), self.line, start_col))

    def _read_number(self) -> None:
        start_col = self.col
        start = self.pos
        has_dot = False
        while self.pos < len(self.source) and (
            self.source[self.pos].isdigit() or self.source[self.pos] == "."
        ):
            if self.source[self.pos] == ".":
                if has_dot:
                    break
                has_dot = True
            self.pos += 1
            self.col += 1
        num_str = self.source[start : self.pos]
        self.tokens.append(
            Token(
                TT.NUMBER,
                float(num_str) if has_dot else int(num_str),
                self.line,
                start_col,
            )
        )

    def _read_ident(self) -> None:
        start_col = self.col
        start = self.pos
        while self.pos < len(self.source) and (
            self.source[self.pos].isalnum() or self.source[self.pos] in "_-"
        ):
            self.pos += 1
            self.col += 1
        word = self.source[start : self.pos]
        tt = KEYWORDS.get(word, TT.IDENT)
        self.tokens.append(Token(tt, word, self.line, start_col))

    def _read_punct(self, ch: str) -> None:
        tt_map = {
            "{": TT.LBRACE,
            "}": TT.RBRACE,
            "[": TT.LBRACKET,
            "]": TT.RBRACKET,
            ":": TT.COLON,
            ";": TT.SEMICOLON,
            ",": TT.COMMA,
        }
        if (
            ch == "-"
            and self.pos + 1 < len(self.source)
            and self.source[self.pos + 1] == ">"
        ):
            self.tokens.append(Token(TT.ARROW, "->", self.line, self.col))
            self.pos += 2
            self.col += 2
        else:
            self.tokens.append(Token(tt_map[ch], ch, self.line, self.col))
            self.pos += 1
            self.col += 1


# ---------------------------------------------------------------------------
# AST nodes
# ---------------------------------------------------------------------------


@dataclass
class AbilityDecl:
    name: str
    category: str = ""
    desc: str = ""
    desc_ru: str = ""
    params: list[str] = field(default_factory=list)


@dataclass
class ParamField:
    key: str
    value: Any


@dataclass
class ParamDecl:
    name: str
    fields: list[ParamField] = field(default_factory=list)


@dataclass
class UnitDecl:
    name: str
    symbol: str = ""
    base: str = ""
    factor: float = 1.0
    offset: float = 0.0


@dataclass
class AlterField:
    key: str
    value: Any


@dataclass
class AlterStmt:
    source: str
    target: str
    fields: list[AlterField] = field(default_factory=list)


@dataclass
class ImportStmt:
    path: str


@dataclass
class Program:
    statements: list[Any] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


class Parser:
    """Parse token stream into AST."""

    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> Program:
        prog = Program()
        while not self._at(TT.EOF):
            if self._at(TT.NEWLINE):
                self._advance()
                continue
            stmt = self._parse_statement()
            if stmt is not None:
                prog.statements.append(stmt)
        return prog

    def _current(self) -> Token:
        return self.tokens[self.pos]

    def _at(self, tt: TT) -> bool:
        return self._current().type == tt

    def _advance(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def _expect(self, tt: TT) -> Token:
        tok = self._current()
        if tok.type != tt:
            raise SyntaxError(
                f"Expected {tt.name}, got {tok.type.name} ('{tok.value}') at {tok.line}:{tok.col}"
            )
        return self._advance()

    def _skip_newlines(self) -> None:
        while self._at(TT.NEWLINE):
            self._advance()

    def _parse_statement(self) -> Any | None:
        tok = self._current()
        if tok.type == TT.ABILITY:
            return self._parse_ability()
        elif tok.type == TT.PARAM:
            return self._parse_param()
        elif tok.type == TT.UNIT:
            return self._parse_unit()
        elif tok.type == TT.ALTER:
            return self._parse_alter()
        elif tok.type == TT.IMPORT:
            return self._parse_import()
        else:
            raise SyntaxError(
                f"Unexpected token {tok.type.name} ('{tok.value}') at {tok.line}:{tok.col}"
            )

    def _parse_ability(self) -> AbilityDecl:
        self._advance()  # consume 'ability'
        name_tok = self._expect(TT.IDENT)
        self._expect(TT.LBRACE)
        decl = AbilityDecl(name=str(name_tok.value))
        self._skip_newlines()
        while not self._at(TT.RBRACE) and not self._at(TT.EOF):
            key_tok = self._advance()
            self._expect(TT.COLON)
            if key_tok.type == TT.CATEGORY:
                decl.category = str(self._expect(TT.STRING).value)
            elif key_tok.type == TT.DESC:
                decl.desc = str(self._expect(TT.STRING).value)
            elif key_tok.type == TT.DESC_RU:
                decl.desc_ru = str(self._expect(TT.STRING).value)
            elif key_tok.type == TT.PARAMS:
                self._expect(TT.LBRACKET)
                while not self._at(TT.RBRACKET):
                    p = self._expect(TT.IDENT)
                    decl.params.append(str(p.value))
                    if self._at(TT.COMMA):
                        self._advance()
                self._expect(TT.RBRACKET)
            else:
                raise SyntaxError(
                    f"Unknown ability field '{key_tok.value}' at {key_tok.line}:{key_tok.col}"
                )
            self._expect(TT.SEMICOLON)
            self._skip_newlines()
        self._expect(TT.RBRACE)
        return decl

    def _parse_param(self) -> ParamDecl:
        self._advance()  # consume 'param'
        name_tok = self._expect(TT.IDENT)
        self._expect(TT.LBRACE)
        decl = ParamDecl(name=str(name_tok.value))
        self._skip_newlines()
        while not self._at(TT.RBRACE) and not self._at(TT.EOF):
            key_tok = self._advance()
            self._expect(TT.COLON)
            if self._at(TT.STRING):
                val = str(self._advance().value)
            elif self._at(TT.NUMBER):
                val = self._advance().value
            elif self._at(TT.IDENT) or self._at(TT.UNIT):
                val = str(self._advance().value)
            elif self._at(TT.LBRACKET):
                self._advance()
                arr: list[float] = []
                while not self._at(TT.RBRACKET):
                    arr.append(float(self._advance().value))
                    if self._at(TT.COMMA):
                        self._advance()
                self._expect(TT.RBRACKET)
                val = arr
            else:
                raise SyntaxError(
                    f"Unexpected value in param field at {self._current().line}:{self._current().col}"
                )
            decl.fields.append(ParamField(key=str(key_tok.value), value=val))
            self._expect(TT.SEMICOLON)
            self._skip_newlines()
        self._expect(TT.RBRACE)
        return decl

    def _parse_unit(self) -> UnitDecl:
        self._advance()  # consume 'unit'
        name_tok = self._expect(TT.IDENT)
        self._expect(TT.LBRACE)
        decl = UnitDecl(name=str(name_tok.value))
        self._skip_newlines()
        while not self._at(TT.RBRACE) and not self._at(TT.EOF):
            key_tok = self._advance()
            self._expect(TT.COLON)
            if key_tok.type == TT.SYMBOL:
                decl.symbol = str(self._expect(TT.STRING).value)
            elif key_tok.type == TT.BASE:
                decl.base = str(self._expect(TT.IDENT).value)
            elif key_tok.type == TT.FACTOR:
                decl.factor = float(self._expect(TT.NUMBER).value)
            elif key_tok.type == TT.OFFSET:
                decl.offset = float(self._expect(TT.NUMBER).value)
            else:
                raise SyntaxError(
                    f"Unknown unit field '{key_tok.value}' at {key_tok.line}:{key_tok.col}"
                )
            self._expect(TT.SEMICOLON)
            self._skip_newlines()
        self._expect(TT.RBRACE)
        return decl

    def _parse_alter(self) -> AlterStmt:
        self._advance()  # consume 'alter'
        src = str(self._expect(TT.IDENT).value)
        self._expect(TT.ARROW)
        tgt = str(self._expect(TT.IDENT).value)
        self._expect(TT.LBRACE)
        stmt = AlterStmt(source=src, target=tgt)
        self._skip_newlines()
        while not self._at(TT.RBRACE) and not self._at(TT.EOF):
            key_tok = self._advance()
            self._expect(TT.COLON)
            if self._at(TT.STRING):
                val = str(self._advance().value)
            elif self._at(TT.NUMBER):
                val = self._advance().value
            elif self._at(TT.IDENT):
                val = str(self._advance().value)
            else:
                raise SyntaxError(
                    f"Unexpected value in alter field at {self._current().line}:{self._current().col}"
                )
            stmt.fields.append(AlterField(key=str(key_tok.value), value=val))
            self._expect(TT.SEMICOLON)
            self._skip_newlines()
        self._expect(TT.RBRACE)
        return stmt

    def _parse_import(self) -> ImportStmt:
        self._advance()  # consume 'import'
        path = str(self._expect(TT.STRING).value)
        return ImportStmt(path=path)


# ---------------------------------------------------------------------------
# Evaluator — walks the AST and applies changes to ability/param registries
# ---------------------------------------------------------------------------


class Evaluator:
    """Interpret a Synthex program against live registries."""

    def __init__(
        self, abilities: dict | None = None, params: dict | None = None
    ) -> None:
        self.abilities = abilities or {}
        self.params = params or {}
        self.units: dict[str, UnitDecl] = {}
        self.definitions: dict[str, Any] = {}

    def run(self, program: Program) -> dict[str, Any]:
        for stmt in program.statements:
            if isinstance(stmt, AbilityDecl):
                self._register_ability(stmt)
            elif isinstance(stmt, ParamDecl):
                self._register_param(stmt)
            elif isinstance(stmt, UnitDecl):
                self._register_unit(stmt)
            elif isinstance(stmt, AlterStmt):
                self._apply_alter(stmt)
            elif isinstance(stmt, ImportStmt):
                pass  # imports resolved externally
        return {
            "abilities": self.abilities,
            "params": self.params,
            "units": self.units,
        }

    def _register_ability(self, decl: AbilityDecl) -> None:
        self.abilities[decl.name] = decl
        self.definitions[decl.name] = decl

    def _register_param(self, decl: ParamDecl) -> None:
        self.params[decl.name] = {f.key: f.value for f in decl.fields}
        self.definitions[decl.name] = decl

    def _register_unit(self, decl: UnitDecl) -> None:
        self.units[decl.name] = decl
        self.definitions[decl.name] = decl

    def _apply_alter(self, stmt: AlterStmt) -> None:
        target = self.params.get(stmt.source) or self.definitions.get(stmt.source)
        if target is None:
            raise KeyError(f"Unknown target '{stmt.source}' for alter")

        for field in stmt.fields:
            if isinstance(target, dict):
                self._alter_dict(target, field)
            elif isinstance(target, ParamDecl):
                self._alter_param(target, field)

    def _alter_dict(self, d: dict, field: AlterField) -> None:
        op = field.key
        if op == "set":
            d["value"] = field.value
        elif op == "add":
            d["value"] = d.get("value", 0) + field.value
        elif op == "mul":
            d["value"] = d.get("value", 0) * field.value
        elif op == "clamp":
            lo = field.value
            hi = field.value
            for f in field if isinstance(field, list) else []:
                pass
            d["value"] = max(lo, min(hi, d.get("value", 0)))
        else:
            d[op] = field.value

    def _alter_param(self, param: ParamDecl, field: AlterField) -> None:
        for f in param.fields:
            if f.key == "default" and field.key in ("set", "add", "mul"):
                if field.key == "set":
                    f.value = field.value
                elif field.key == "add":
                    f.value = float(f.value) + field.value
                elif field.key == "mul":
                    f.value = float(f.value) * field.value
                return
        param.fields.append(ParamField(key=field.key, value=field.value))


# ---------------------------------------------------------------------------
# Convenience: compile + run in one step
# ---------------------------------------------------------------------------


def execute(
    source: str, abilities: dict | None = None, params: dict | None = None
) -> dict[str, Any]:
    """Parse and evaluate Synthex source string."""
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    return Evaluator(abilities, params).run(ast)


# ---------------------------------------------------------------------------
# Pretty-printer
# ---------------------------------------------------------------------------


def dump(program: Program) -> str:
    """Pretty-print an AST back to Synthex source."""
    lines: list[str] = []
    for stmt in program.statements:
        if isinstance(stmt, AbilityDecl):
            lines.append(f"ability {stmt.name} {{")
            if stmt.category:
                lines.append(f'  category: "{stmt.category}";')
            if stmt.desc:
                lines.append(f'  desc: "{stmt.desc}";')
            if stmt.desc_ru:
                lines.append(f'  desc_ru: "{stmt.desc_ru}";')
            if stmt.params:
                lines.append(f"  params: [{', '.join(stmt.params)}];")
            lines.append("}")
        elif isinstance(stmt, ParamDecl):
            lines.append(f"param {stmt.name} {{")
            for f in stmt.fields:
                v = f'"{f.value}"' if isinstance(f.value, str) else str(f.value)
                lines.append(f"  {f.key}: {v};")
            lines.append("}")
        elif isinstance(stmt, UnitDecl):
            lines.append(f"unit {stmt.name} {{")
            if stmt.symbol:
                lines.append(f'  symbol: "{stmt.symbol}";')
            if stmt.base:
                lines.append(f"  base: {stmt.base};")
            lines.append(f"  factor: {stmt.factor};")
            lines.append(f"  offset: {stmt.offset};")
            lines.append("}")
        elif isinstance(stmt, AlterStmt):
            lines.append(f"alter {stmt.source} -> {stmt.target} {{")
            for f in stmt.fields:
                v = f'"{f.value}"' if isinstance(f.value, str) else str(f.value)
                lines.append(f"  {f.key}: {v};")
            lines.append("}")
        elif isinstance(stmt, ImportStmt):
            lines.append(f'import "{stmt.path}"')
        lines.append("")
    return "\n".join(lines)
