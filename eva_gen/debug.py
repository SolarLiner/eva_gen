from eva_gen.common.front_end import parser

P = parser.Parser("2*(3 + a)")

print(P.parse())
