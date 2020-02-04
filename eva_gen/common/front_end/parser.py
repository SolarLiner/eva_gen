from typing import Union

from common.ast.nodes import *
from common.front_end.lexer import Token, Lexer, ParseError


class Parser:
    def __init__(self, code: Union[str, Lexer], incomplete=False):
        if isinstance(code, Lexer):
            self.lexer = code
        else:
            self.lexer = Lexer(code)
        if incomplete:
            self.token = next(self.lexer)
        else:
            self.token: Token = "_SOI", ""

    @property
    def position(self):
        return self.lexer.linecol

    @property
    def code(self):
        return self.lexer.code

    def parse(self) -> CodeBlockNode:
        start = self.position
        self.eat("_SOI")

        def gen():
            while not self.is_next("_EOI"):
                yield self.parse_function()

        block = list(gen())
        self.eat("_EOI")
        return CodeBlockNode(Span(start, self.position), block)

    def peek(self) -> str:
        return self.token[0]

    def eat(self, token: str) -> str:
        cur_token = self.peek()
        if cur_token == token:
            value = self.token[1]
            try:
                self.token = next(self.lexer)
            except StopIteration:
                self.token = "_EOI", ""
            return value
        if cur_token == "_EOI":
            raise ParseError(
                f"Unexpected end of file, expecting {token}", self.lexer.cur_line, self.position)
        raise ParseError(
            f"Unexpected token {self.token[0]}, expecting {token}", self.lexer.cur_line, self.position)

    def is_next(self, token: str) -> bool:
        return self.peek() == token

    def accept(self, token: str) -> bool:
        if self.is_next(token):
            self.eat(token)
            return True
        return False

    def parse_function(self) -> BaseNode:
        start = self.position
        is_extern = self.accept("KW_EXTERN")
        if self.accept("KW_FUN"):
            name = self.eat("IDENT")
            self.eat("LEFT_PARENT")
            args = self.parse_comma_list()
            self.eat("RIGHT_PARENT")
            if not is_extern:
                code = self.parse_codeblock(force=True)
                return FunctionNode(Span(start, self.position), name, args, code)
            else:
                return ExternFunctionNode(Span(start, self.position), name, args)
        return self.parse_codeblock()

    def parse_codeblock(self, force=False) -> CodeBlockNode:
        start = self.position
        if self.accept("LEFT_BRACE"):

            def gen():
                while not self.is_next("RIGHT_BRACE"):
                    yield self.parse_statement()

            block = list(gen())
            self.eat("RIGHT_BRACE")
        else:
            if force:
                raise ParseError(f"Code block need braces",
                                 self.lexer.cur_line, self.position)
            block = [self.parse_declaration()]
        return CodeBlockNode(Span(start, self.position), block)

    def parse_statement(self) -> BaseNode:
        start = self.position
        if self.accept("KW_RETURN"):
            expr = self.parse_expression()
            return ReturnStatementNode(Span(start, self.position), expr)
        if self.accept("KW_WHILE"):
            cond = self.parse_expression()
            block = self.parse_codeblock()
            return WhileNode(Span(start, self.position), cond, block)
        return self.parse_declaration()

    def parse_declaration(self) -> BaseNode:
        start = self.position
        if self.accept("KW_VAR"):
            ident = self.eat("IDENT")
            return DeclarationNode(Span(start, self.position), ident)
        return self.parse_assignment()

    def parse_assignment(self) -> BaseNode:
        start = self.position
        left = self.parse_expression()
        if self.accept("EQUALS"):
            if not isinstance(left, IdentNode):
                raise ParseError(
                    "Syntax error", self.lexer.cur_line, self.position)
            expr = self.parse_expression()
            return AssignmentNode(Span(start, self.position), left.ident, expr)
        return left

    def parse_expression(self) -> ExprNode:
        if self.accept("LEFT_PARENT"):
            e = self.parse_expression()
            self.eat("RIGHT_PARENT")
            return e

        return self.parse_expr_add()

    def parse_expr_add(self) -> ExprNode:
        start = self.position
        left = self.parse_expr_sub()
        if self.accept("BIN_ADD"):
            right = self.parse_expr_add()
            return BinaryOperationNode(Span(start, self.position), left, BinaryOperation.ADD, right)
        return left

    def parse_expr_sub(self) -> ExprNode:
        start = self.position
        left = self.parse_expr_mult()
        if self.accept("BIN_SUB"):
            right = self.parse_expr_add()
            return BinaryOperationNode(Span(start, self.position), left, BinaryOperation.SUB, right)
        return left

    def parse_expr_mult(self) -> ExprNode:
        start = self.position
        left = self.parse_expr_div()
        if self.accept("BIN_MULT"):
            right = self.parse_expr_mult()
            return BinaryOperationNode(Span(start, self.position), left, BinaryOperation.MULT, right)
        return left

    def parse_expr_div(self) -> ExprNode:
        start = self.position
        left = self.parse_expr_power()
        if self.accept("BIN_DIV"):
            right = self.parse_expr_mult()
            return BinaryOperationNode(Span(start, self.position), left, BinaryOperation.DIV, right)
        return left

    def parse_expr_power(self):
        start = self.position
        left = self.parse_function_call()
        if self.accept("BIN_POWER"):
            right = self.parse_expr_power()
            return BinaryOperationNode(Span(start, self.position), left, BinaryOperation.POWER, right)
        return left

    def parse_function_call(self) -> ExprNode:
        start = self.position
        left = self.parse_expr_unary()
        if self.accept("LEFT_PARENT"):
            if not isinstance(left, IdentNode):
                raise ParseError(
                    "Syntax error", self.lexer.cur_line, self.position)
            args = self.parse_comma_list("RIGHT_PARENT")
            self.eat("RIGHT_PARENT")
            return FunctionCallNode(Span(start, self.position), left.ident, args)
        return left

    def parse_expr_unary(self) -> ExprNode:
        start = self.position
        if self.is_next("UNOP"):
            op = self.eat("UNOP")
            operand = self.parse_function_call()
            return UnaryOperationNode(Span(start, self.position), UnaryOperation(op), operand)
        return self.parse_parent_expr()

    def parse_parent_expr(self):
        if self.accept("LEFT_PARENT"):
            e = self.parse_expression()
            self.eat("RIGHT_PARENT")
            return e
        return self.parse_value()

    def parse_value(self) -> ExprNode:
        start = self.position
        if self.is_next("NUMBER"):
            value = self.eat("NUMBER")
            return ValueNode(Span(start, self.position), value)
        if self.is_next("IDENT"):
            ident = self.eat("IDENT")
            return IdentNode(Span(start, self.position), ident)
        raise ParseError(
            "Syntax error", self.lexer.get_line(start.line), start)

    def parse_comma_list(self, close_token="RIGHT_PARENT"):
        if self.is_next(close_token):
            return list()
        args = [self.parse_expression()]
        while self.accept("COMMA"):
            args.append(self.parse_expression())

        return args
