from types import FunctionType
from typing import List, Tuple, Set

from lexer.lexer import Lexer
from parser.node import FunctionCallNode, Nothing, TypeNode, FunctionTypeNode, TraitFunctionNode, VarDefNode, \
    FuncDefNode, TypeDefNode, DataInitNode, TraitConstraintNode, TypeAnnotationNode, TypeVarNode
from parser.scope import Scope, ScopeManager
from parser.symbol import Symbol, TypeSymbol, FunctionSymbol, TraitSymbol
from parser.types import Type, FunctionSignature, StructureType, TraitConstraintsType, TypeVar


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



def extract_type_from_ast(ast_node: TypeNode | FunctionTypeNode | TraitFunctionNode | VarDefNode | List | FuncDefNode | TypeDefNode | TypeAnnotationNode | TypeVarNode, type_vars: set[str]=None) -> Type | FunctionSignature | Tuple[Type | FunctionSignature, ...] | StructureType:
    type_vars = type_vars or set()
    def helper(ast):
        if isinstance(ast, TypeVarNode):
            return TypeVar(ast.identifier.name)
        if type(ast) in (list, set, tuple):
            return tuple(helper(x) for x in ast)
        elif type(ast) is TypeNode:
            return TypeVar(ast.name) if ast.name in type_vars else Type(ast.name, args=helper(ast.type_parameters))
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
        elif type(ast) in (TypeDefNode, TypeAnnotationNode) :
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
    scope_manager.global_scope.add(FunctionSymbol("echo", FunctionSignature((Type("Any"),), Type("Unit")), native_call=print))
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
    if expect_type.name == "Any" or actual_type.name == "Any":
        return False
    # 否则直接比较类型是否相等
    return expect_type != actual_type


def died_branch():
    raise Exception("can not reach here")

def indent(strings: List[str]|str, size=1) -> str:
    if isinstance(strings, str):
        strings = strings.split("\n")
    return "\n".join([f"{'    ' * size}{s}" for s in strings])

