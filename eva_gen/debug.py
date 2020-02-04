from common.front_end import parser, lexer

P = parser.Parser("2*(3 + a)")

print(P.parse())
