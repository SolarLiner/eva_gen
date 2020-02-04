import re
from collections import namedtuple
from typing import Dict, AnyStr, Tuple, Pattern, Iterator

TokenSpec = Dict[str, Pattern]
Token = Tuple[str, str]
LineCol = namedtuple("LineCol", "line col")


class ParseError(Exception):
    def __init__(self, message: AnyStr, line: str, position: LineCol):
        line_str = str(position.line)
        caret = ' ' * (position.col + len(line_str)) + '^'
        super().__init__(f"{message}\n{line_str}| {line}\n{caret}")
        self.position = position


TOKENS: TokenSpec = {
    "UNOP": re.compile("not"),
    "BIN_POWER": re.compile(r"\*\*"),
    "BIN_MULT": re.compile(r"\*"),
    "BIN_DIV": re.compile(r"/"),
    "BIN_ADD": re.compile(r"\+"),
    "BIN_SUB": re.compile(r"-"),
    "KW_VAR": re.compile(r"var"),
    "KW_FUN": re.compile(r"fun"),
    "KW_WHILE": re.compile(r"while"),
    "KW_RETURN": re.compile(r"return"),
    "KW_EXTERN": re.compile("extern"),
    "IDENT": re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*"),
    "NUMBER": re.compile(r"([0-9]+(\.[0-9]+)?|0x[0-9A-F]+|0o[0-7]+)"),
    "EQUALS": re.compile(r"="),
    "LESSTHAN": re.compile(r"<"),
    "LESSEQUAL": re.compile(r"<="),
    "GREATERTHAN": re.compile(r">"),
    "GREATEREQUAL": re.compile(r">="),
    "LEFT_PARENT": re.compile(r"\("),
    "RIGHT_PARENT": re.compile(r"\)"),
    "LEFT_BRACE": re.compile(r"{"),
    "RIGHT_BRACE": re.compile(r"}"),
    "COMMA": re.compile(r","),
    "_IGNORE": re.compile(r"[ \t\n]+"),
}


class Lexer(Iterator[Token]):
    def __init__(self, code: AnyStr):
        self.code = code
        self.rest = code
        self.position = 0

    def __next__(self) -> Token:
        if len(self.rest) == 0:
            raise StopIteration
        go_again = True
        while go_again:
            go_again = False
            for k, v in TOKENS.items():
                m = v.match(self.rest)
                if m and m.start(0) == 0:
                    self.rest = self.rest[m.end(0):]
                    self.position = len(self.code) - len(self.rest)
                    if k == "_IGNORE":
                        go_again = True
                        break
                    return k, m.group(0)
        if len(self.rest) == 0:
            raise StopIteration
        raise ParseError(f"Cannot lex input code", self.cur_line, self.linecol)

    def linecol_from_position(self, position: int) -> LineCol:
        curpos = 0
        lines = self.code.split("\n")
        for i, line in enumerate(lines):
            if curpos + len(line) >= position:
                line = i + 1
                col = position - curpos + 1
                return LineCol(line, col)
            else:
                curpos += len(line)
        line = len(lines)
        col = len(lines[-1])
        return LineCol(line, col)

    @property
    def linecol(self) -> LineCol:
        return self.linecol_from_position(self.position)

    def get_line(self, lineno: int) -> str:
        for i, line in enumerate(self.code.split("\n")):
            if i + 1 == lineno:
                return line
        raise ValueError(f"Bad line number: {lineno}")

    @property
    def cur_line(self) -> str:
        return self.get_line(self.linecol.line)
