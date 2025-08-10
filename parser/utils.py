from typing import List, Tuple, Set, Callable

from lexer.lexer import Lexer
from parser.node import  Nothing, FunctionTypeNode, TraitFunctionNode, VarDefNode, \
    FunctionDefNode, StructDefNode, TraitConstraintNode, TypeAnnotation, TypeVarNode
from parser.scope import Scope, ScopeManager
from parser.symbol import Symbol, TypeSymbol, FunctionSymbol, TraitSymbol, VarSymbol
from parser.symbol_type import PrimitiveType, TypeRef, FunctionTypeRef, TypeVar, TraitTypeRef


# from parser.types import Type, FunctionSignature, StructureType, TraitConstraintsType


class RepeatParser:

    def __init__(self, split: str, end: str):
        self.split = split
        self.end = end

    def parse[T](self, lexer: Lexer, parser: Callable[[Lexer], T]) -> List[T]:
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



# def extract_type_from_ast(ast_node: StructNode | FunctionTypeNode | TraitFunctionNode | VarDefNode | List | FunctionDefNode | StructDefNode | TypeNameAndParamNode | TypeVarNode, type_vars: set[str]=None) -> Type | FunctionSignature | Tuple[Type | FunctionSignature, ...] | StructureType:
#     type_vars = type_vars or set()
#     def helper(ast):
#         if isinstance(ast, TypeVarNode):
#             return TypeVar(ast.name.string)
#         if type(ast) in (list, set, tuple):
#             return tuple(helper(x) for x in ast)
#         elif type(ast) is StructNode:
#             return TypeVar(ast.string) if ast.string in type_vars else Type(ast.string, args=helper(ast.parameters))
#         elif type(ast) is FunctionTypeNode:
#             return FunctionSignature(
#                 tuple([helper(x) for x in ast.args]),
#                 helper(ast.return_type)
#             )
#         elif type(ast) is TraitFunctionNode:
#             return FunctionSignature(
#                 tuple([helper(x) for x in ast.args]),
#                 helper(ast.return_type)
#             )
#         elif type(ast) is FunctionDefNode:
#             return FunctionSignature(
#                 helper(ast.args),
#                 helper(ast.return_type)
#             )
#         elif type(ast) is VarDefNode:
#             return helper(ast.var_type)
#         elif type(ast) in (StructDefNode, TypeNameAndParamNode) :
#             return StructureType({id_node.string: helper(type_node) for id_node, type_node in ast.type_def})
#         elif type(ast) is TraitConstraintNode:
#             return TraitConstraintsType([x.string.string for x in ast.traits])
#         else:
#             raise Exception("can not reach here")
#     return helper(ast_node)
#
#
# def get_type_from_ast(ast_node: StructNode | FunctionTypeNode | TraitFunctionNode | VarDefNode | List | FunctionDefNode | StructDefNode | TypeNameAndParamNode | TypeVarNode, type_vars: set[str]=None):
#     def helper(ast):
#         if isinstance(ast, TypeVarNode):
#             return TypeVar(ast.name.string)
#         if type(ast) in (list, set, tuple):
#             return tuple(helper(x) for x in ast)
#         elif type(ast) is StructNode:
#             return TypeVar(ast.string) if ast.string in type_vars else Type(ast.string, args=helper(ast.parameters))
#         elif type(ast) is FunctionTypeNode:
#             return FunctionSignature(
#                 tuple([helper(x) for x in ast.args]),
#                 helper(ast.return_type)
#             )
#         elif type(ast) is TraitFunctionNode:
#             return FunctionSignature(
#                 tuple([helper(x) for x in ast.args]),
#                 helper(ast.return_type)
#             )
#         elif type(ast) is FunctionDefNode:
#             return FunctionSignature(
#                 helper(ast.args),
#                 helper(ast.return_type)
#             )
#         elif type(ast) is VarDefNode:
#             return helper(ast.var_type)
#         elif type(ast) in (StructDefNode, TypeNameAndParamNode):
#             return StructureType({id_node.string: helper(type_node) for id_node, type_node in ast.type_def})
#         elif type(ast) is TraitConstraintNode:
#             return TraitConstraintsType([x.string.string for x in ast.traits])
#         else:
#             raise Exception("can not reach here")
#
#     return helper(ast_node)

PRIMITIVE_TYPE_NAME = [
    "Int",
    "String",
    "Float",
    "Bool",
    "Unit",
    "Any"
]

def init_global_scope(scope_manager: ScopeManager):

    for t in PRIMITIVE_TYPE_NAME:
        scope_manager.add_type(TypeSymbol(t, define=PrimitiveType(t), parameters=[]))
    scope_manager.add_symbol(FunctionSymbol("echo", FunctionTypeRef("echo", [TypeRef("String")], TypeRef("Unit"))))
    scope_manager.add_symbol(FunctionSymbol("as_string", FunctionTypeRef("as_string", [TypeRef("any")], TypeRef("String"))))
    scope_manager.add_symbol(FunctionSymbol("as_float", FunctionTypeRef("as_float", [TypeRef("any")], TypeRef("Float"))))

    scope_manager.add_symbol(
        FunctionSymbol("add_int", FunctionTypeRef("add_int", [TypeRef("Int"), TypeRef("Int")], TypeRef("Int"))))

    scope_manager.add_symbol(
        FunctionSymbol("sub_int", FunctionTypeRef("sub_int", [TypeRef("Int"), TypeRef("Int")], TypeRef("Int"))))

    scope_manager.add_symbol(
        FunctionSymbol("div_int", FunctionTypeRef("div_int", [TypeRef("Int"), TypeRef("Int")], TypeRef("Int"))))

    scope_manager.add_symbol(
        FunctionSymbol("mul_int", FunctionTypeRef("mul_int", [TypeRef("Int"), TypeRef("Int")], TypeRef("Int"))))


    scope_manager.add_symbol(
        FunctionSymbol("add_float", FunctionTypeRef("add_float", [TypeRef("Float"), TypeRef("Float")], TypeRef("Float"))))

    scope_manager.add_symbol(
        FunctionSymbol("sub_float", FunctionTypeRef("sub_float", [TypeRef("Float"), TypeRef("Float")], TypeRef("Float"))))

    scope_manager.add_symbol(
        FunctionSymbol("div_float", FunctionTypeRef("div_float", [TypeRef("Float"), TypeRef("Float")], TypeRef("Float"))))

    scope_manager.add_symbol(
        FunctionSymbol("mul_float", FunctionTypeRef("mul_float", [TypeRef("Float"), TypeRef("Float")], TypeRef("Float"))))

    scope_manager.add_symbol(
        FunctionSymbol("panic",
                       FunctionTypeRef("panic", [TypeRef("String")], TypeRef("Unit"))))

    scope_manager.add_symbol(
        FunctionSymbol("le_int", FunctionTypeRef("le_int", [TypeRef("Int"), TypeRef("Int")], TypeRef("Bool"))))

    scope_manager.add_symbol(
        FunctionSymbol("gt_int", FunctionTypeRef("le_int", [TypeRef("Int"), TypeRef("Int")], TypeRef("Bool"))))

    scope_manager.add_symbol(
        FunctionSymbol("eq_int", FunctionTypeRef("le_int", [TypeRef("Int"), TypeRef("Int")], TypeRef("Bool"))))

    scope_manager.add_type(TypeSymbol("List", define=TypeRef("List"), parameters=[TypeVar.create("T")]))

    # var1 = TypeVar.create("T", constraints=[TraitTypeRef("Write")])
    #
    # scope_manager.add_symbol(FunctionSymbol("next_item",
    #                    FunctionTypeRef(
    #                        "next_item",
    #                        args =[var1],
    #                        return_type=var1
    #                    ))
    #                        )


    # scope_manager.add_symbol(
    #     FunctionSymbol("add_float", FunctionTypeRef("add_float", [TypeRef("Float")], TypeRef("Float"))))

    # scope_manager.add_type(TypeSymbol("Int", define=PrimitiveType("Int")))
    # scope_manager.add_struct(TypeSymbol("String"))
    # scope_manager.add_struct(TypeSymbol("Float"))
    # scope_manager.add_struct(TypeSymbol("Bool"))
    # scope_manager.add_struct(TypeSymbol("Unit"))
    # scope_manager.global_scope.add(FunctionSymbol("echo", FunctionSignature((Type("Any"),), Type("Unit")), native_call=print))
    # scope_manager.add_trait(
    #     TraitSymbol(
    #         "Write",
    #         "T",
    #         {
    #             'toString': FunctionSignature((), Type("String"), True)
    #         }
    #     )
    # )
    # scope_manager.add_trait(
    #     TraitSymbol(
    #         "Read",
    #         "T",
    #         {
    #             'toString': FunctionSignature((Type("String"),), Type("T"), True)
    #         }
    #     )
    # )


# def type_check(expect_type: Type|TraitConstraintsType, actual_type: Type, scope: Scope) -> bool|Set[str]:
#     if isinstance(expect_type, TraitConstraintsType):
#         impled_traits = scope.get_impl_by_target(actual_type.name) or {}
#         impled_trait_names = set(impled_traits.keys())
#         constraints = set(expect_type.constraints)
#         return constraints - impled_trait_names
#     if expect_type.name == "Any" or actual_type.name == "Any":
#         return False
#     # 否则直接比较类型是否相等
#     return expect_type != actual_type


def died_branch():
    raise Exception("can not reach here")

def indent(strings: List[str]|str, size=1) -> str:
    if isinstance(strings, str):
        strings = strings.split("\n")
    return "\n".join([f"{'    ' * size}{s}" for s in strings])


