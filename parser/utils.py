from lexer.lexer import Lexer
from parser.node import FunctionCallNode, Nothing
from parser.scope import Scope
from parser.symbol import Symbol, TypeSymbol, FunctionSymbol


class RepeatParser:

    def __init__(self, split: str, end: str):
        self.split = split
        self.end = end

    def parse(self, lexer: Lexer, parser):
        res = []
        if lexer.try_peek(self.end):
            lexer.pop()
            return res
        while True:
            node = parser(lexer)
            res.append(node)
            if lexer.peek().token_type == self.split:
                lexer.pop()
            if lexer.peek().token_type == self.end:
                lexer.pop()
                break
        return res


def combiner(*parsers):
    def parse(lexer: Lexer):
        res = []
        for parser in parsers:
            node = parser(lexer)
            if type(node) is not Nothing:
                res.append(node)
        return res
    return parse


def init_global_scope():
    global_scope = Scope()
    global_scope.add(TypeSymbol("Int"))
    global_scope.add(TypeSymbol("String"))
    global_scope.add(TypeSymbol("Float"))
    global_scope.add(TypeSymbol("Bool"))
    global_scope.add(TypeSymbol("Unit"))
    global_scope.add(FunctionSymbol("print", ("String",), native_call=print))
    return global_scope