from types import FunctionType
from typing import List, Tuple, Set

from lexer.lexer import Lexer
from parser.node import FunctionCallNode, Nothing, TypeNode, FunctionTypeNode, TraitFunctionNode, VarDefNode, \
    FuncDefNode, TypeDefNode, DataInitNode, TraitConstraintNode
from parser.scope import Scope, ScopeManager
from parser.symbol import Symbol, TypeSymbol, FunctionSymbol, TraitSymbol
from parser.types import Type, FunctionSignature, StructureType, TraitConstraintsType


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
            lexer.expect(self.split, self.end)
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


def extract_type_from_ast(ast_node: TypeNode | FunctionTypeNode | TraitFunctionNode| VarDefNode| List | FuncDefNode | TypeDefNode) -> Type | FunctionSignature | Tuple[Type | FunctionSignature, ...] | StructureType:
    def helper(ast):
        if type(ast) in (list, set, tuple):
            return tuple(helper(x) for x in ast)
        elif type(ast) is TypeNode:
            return Type(ast.name)
        elif type(ast) is FunctionTypeNode:
            return FunctionSignature(
                tuple([helper(x) for x in ast.args]),
                helper(ast.return_type)
            )
        elif type(ast) is TraitFunctionNode:
            return FunctionSignature(
                tuple([helper(x) for x in ast.args]),
                helper(ast.return_type)
            )
        elif type(ast) is FuncDefNode:
            return FunctionSignature(
                helper(ast.args),
                helper(ast.return_type)
            )
        elif type(ast) is VarDefNode:
            return helper(ast.var_type)
        elif type(ast) is TypeDefNode:
            return StructureType({id_node.name: helper(type_node) for id_node, type_node in ast.type_def})
        elif type(ast) is TraitConstraintNode:
            return TraitConstraintsType([x.name.name for x in ast.traits])
        else:
            raise Exception("can not reach here")
    return helper(ast_node)


def init_global_scope(scope_manager: ScopeManager):
    scope_manager.add_type(TypeSymbol("Int"))
    scope_manager.add_type(TypeSymbol("String"))
    scope_manager.add_type(TypeSymbol("Float"))
    scope_manager.add_type(TypeSymbol("Bool"))
    scope_manager.add_type(TypeSymbol("Unit"))
    scope_manager.global_scope.add(FunctionSymbol("echo", FunctionSignature((Type("String"),), Type("Unit")), native_call=print))
    scope_manager.add_trait(
        TraitSymbol(
            "Write",
            "T",
            {
                'toString': FunctionSignature((), Type("String"), True)
            }
        )
    )
    scope_manager.add_trait(
        TraitSymbol(
            "Read",
            "T",
            {
                'toString': FunctionSignature((Type("String"),), Type("T"), True)
            }
        )
    )


def type_check(expect_type: Type|TraitConstraintsType, actual_type: Type, scope: Scope) -> bool|Set[str]:
    if isinstance(expect_type, TraitConstraintsType):
        impled_traits = scope.get_impl_by_target(actual_type.name) or {}
        impled_trait_names = set(impled_traits.keys())
        constraints = set(expect_type.constraints)
        return constraints - impled_trait_names
        # if not_implemented:
        #     raise TypeConstraintError(f"Type constraints check failed. "
        #                               f"trait {not_implemented} is not implement in type `{actual_type}`.\n" + self.error_reporter.mark(
        #         node.args[index], context_node=node))
    # 否则直接比较类型是否相等
    return expect_type != actual_type
        # raise TypeError(f"Expected type `{expect_type}` but got type `{actual_type}`.\n" + self.error_reporter.mark(
        #     node.args[index], context_node=node))

def died_branch():
    raise Exception("can not reach here")

def indent(strings: List[str]|str, size=1) -> str:
    if isinstance(strings, str):
        strings = strings.split("\n")
    return "\n".join([f"{'    ' * size}{s}" for s in strings])
