import abc
import typing
from dataclasses import dataclass
from enum import Enum
from typing import Any, List

from ..front_end.lexer import LineCol

Visitor = typing.Callable[["BaseNode"], Any]
ExprNode = typing.Union[
    "IdentNode",
    "ValueNode",
    "UnaryOperationNode",
    "BinaryOperationNode",
    "FunctionCallNode",
]


class BinaryOperation(Enum):
    ADD = "+"
    SUB = "-"
    MULT = "*"
    DIV = "/"
    POWER = "**"
    AND = "and"
    OR = "or"


class UnaryOperation(Enum):
    PRINT = "print"
    NOT = "not"


@dataclass
class Span:
    start: LineCol
    end: LineCol


class BaseNode(abc.ABC):
    def __init__(self, span: Span):
        self.span = span

    def visit(self, visitor: Visitor):
        visitor(self)

    def __eq__(self, other):
        if type(self) is type(other):
            return self.__dict__ == other.__dict__
        return NotImplemented

    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self.__dict__)}"

    @abc.abstractmethod
    def display(self, n: int):
        pass

    def __str__(self):
        return f"{self.display(0)}"


class DeclarationNode(BaseNode):
    def __init__(self, span: Span, ident: str):
        super().__init__(span)
        self.ident = ident

    def display(self, n: int):
        return f"{n*'  '}var {self.ident}\n"


class AssignmentNode(BaseNode):
    def __init__(self, span: Span, ident: str, expr: ExprNode):
        super().__init__(span)
        self.ident = ident
        self.expr = expr

    def display(self, n: int):
        return f"{n * '  '}var {self.ident} =\n{self.expr.display(n + 1)}"


class ValueNode(BaseNode):
    def __init__(self, span: Span, value: str):
        super().__init__(span)
        self.value = float(value)

    def display(self, n: int):
        return f"{n*'  '}{self.value}\n"


class BinaryOperationNode(BaseNode):
    def __init__(
        self, span: Span, left: ExprNode, op: BinaryOperation, right: ExprNode
    ):
        super().__init__(span)
        self.left = left
        self.op = op
        self.right = right

    def visit(self, visitor: Visitor):
        visitor(self.left)
        visitor(self.right)
        super().visit(visitor)

    def display(self, n):
        return f"{n*'  '}{self.op}\n{self.left.display(n+1)}{self.right.display(n+1)}"


class UnaryOperationNode(BaseNode):
    def __init__(self, span: Span, op: UnaryOperation, operand: ExprNode):
        super().__init__(span)
        self.op = op
        self.operand = operand

    def visit(self, visitor: Visitor):
        visitor(self.operand)
        super().visit(visitor)

    def display(self, n: int):
        return f"{n*'  '}{self.op}\n{self.operand.display(n+1)}"


class ReturnStatementNode(BaseNode):
    def __init__(self, span: Span, expr: ExprNode):
        super().__init__(span)
        self.expr = expr

    def visit(self, visitor: Visitor):
        visitor(self.expr)
        super().visit(visitor)

    def display(self, n: int):
        return f"{n*'  '}return\n{self.expr.display(n+1)}"


class CodeBlockNode(BaseNode):
    def __init__(self, span: Span, block: typing.List[BaseNode]):
        super().__init__(span)
        self.block = block

    def visit(self, visitor: Visitor):
        [visitor(b) for b in self.block]
        super().visit(visitor)

    def display(self, n: int):
        s = "".join(node.display(n + 1) for node in self.block)
        return f"{n*'  '}block\n{s}"


class WhileNode(BaseNode):
    def __init__(self, span: Span, cond: ExprNode, block: CodeBlockNode):
        super().__init__(span)
        self.condition = cond
        self.block = block

    def visit(self, visitor: Visitor):
        visitor(self.condition)
        visitor(self.block)
        super().visit(visitor)

    def display(self, n: int):
        return f"{n*'  '}while\n{self.condition.display(n+1)}{self.block.display(n+1)}"


class IdentNode(BaseNode):
    def __init__(self, span: Span, ident: str):
        super().__init__(span)
        self.ident = ident

    def display(self, n: int):
        return f"{n * '  '}{self.ident}\n"


class FunctionNode(BaseNode):
    def __init__(
        self, span: Span, name: str, args: List[ExprNode], code: CodeBlockNode
    ):
        super().__init__(span)
        self.name = name
        self.args = args
        self.block = code

    def visit(self, visitor: Visitor):
        for arg in self.args:
            visitor(arg)
        visitor(self.block)
        super().visit(visitor)

    def display(self, n: int):
        return f"{n * '  '}function {self.name}(nargs={len(self.args)})\n{self.block.display(n + 1)}"


class ExternFunctionNode(BaseNode):
    def __init__(self, span: Span, name: str, args: List[ExprNode]):
        super().__init__(span)
        self.name = name
        self.args = args

    def display(self, n: int):
        return f"{n * '  '}extern function {self.name}(nargs={len(self.args)})\n"

    def visit(self, visitor: Visitor):
        [visitor(arg) for arg in self.args]
        super().visit(visitor)


class FunctionCallNode(BaseNode):
    def __init__(self, span: Span, ident: str, args: List[ExprNode]):
        super().__init__(span)
        self.ident = ident
        self.args = args

    def visit(self, visitor: Visitor):
        [visitor(a) for a in self.args]
        super().visit(visitor)

    def display(self, n: int):
        s = "".join(node.display(n + 1) for node in self.args)
        return f"{n*'  '}call {self.ident}\n{s}"
