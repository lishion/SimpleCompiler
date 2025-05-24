from lexer.tokendef import Token
from parser import utils
from parser.node import ASTNode, BinaryOpNode, LiteralNode, BlockNode, FunctionCallNode, IdNode, IndexNode, \
    LitArrayNode, LitDictNode, IfStatement, LoopStatement, FuncDefNode, ProcNode, AssignNode, VarDefNode, \
    TypeNode, TypeDefNode, VarNode, Nothing, ReturnNode, DataInitNode, FunctionTypeNode, TraitNode, TraitDefNode, \
    TraitFunctionNode, TraitImplNode, TraitConstraintNode, AttributeNode
from lexer.lexer import Lexer
from typing import Optional, List
from parser.utils import RepeatParser, combiner


def drop(token: str):
    def parse(lexer: Lexer):
        return Nothing(lexer.expect_pop(token))
    return parse

def parse_index(target_token: Token, lexer: Lexer):
    index_node = parse_or(lexer)
    lexer.expect("]")
    lexer.pop()
    target_node = VarNode(target_token.text)
    return IndexNode(target_node, index_node)

def parse_array(lexer: Lexer):
    lexer.expect("[")
    lexer.pop()
    nodes = []
    while True:
        token = lexer.peek()
        if token == "]":
            break
        nodes.append(parse_or(lexer))
        if lexer.peek().token_type == ",":
            lexer.pop()
        if lexer.peek().token_type == "]":
            lexer.pop()
            break
    return LitArrayNode(nodes)

def parse_dict(lexer: Lexer):
    lexer.expect("{")
    lexer.pop()
    nodes = []
    while True:
        token = lexer.peek()
        if token == "}":
            break
        k = parse_or(lexer)
        lexer.expect(":", pop=True)
        v = parse_or(lexer)
        nodes.append((k, v))
        if lexer.peek().token_type == ",":
            lexer.pop()
        if lexer.peek().token_type == "}":
            lexer.pop()
            break
    return LitDictNode(nodes)

def parse_data_init(lexer: Lexer):
    type_node = parse_type(lexer)
    lexer.expect_pop("{")
    body = RepeatParser(",", "}").parse(lexer, combiner(parse_var, drop(":"), parse_expr))
    return DataInitNode(type_node, [AssignNode(var, expr) for var, expr in body])


def parse_expr_unit(lexer: Lexer):
    if lexer.peek() == Lexer.EOF:
        return None
    if lexer.peek().token_type == "(":
        lexer.pop()
        res = parse_add(lexer)
        lexer.expect(")")
        lexer.pop()
        return res
    elif lexer.peek().token_type == "[":
        return parse_array(lexer)
    elif lexer.peek().token_type == "{":
        return parse_dict(lexer)
    lexer.expect('float', 'int', 'string', 'id', 'self')
    token = lexer.peek()
    if token.token_type == "id" or token.token_type == "self":
        node = VarNode(parse_identifier(lexer))
        node.is_self = token.token_type == "self"
        # need to check whether a struct init expr like
        if lexer.try_peek("{"):
            lexer.pop()
            if lexer.try_peek("}"):
                lexer.unpop() # return to {
                return node
                # if a{} then {} should b a block
            else:
                # if a{x:} then should a struct init expr
                if lexer.try_peek("id"):
                    lexer.pop()
                    if lexer.try_peek(":"):
                        lexer.unpop()
                        lexer.unpop()
                        lexer.unpop()
                    return parse_data_init(lexer)
                # otherwise should be a {xxxx}, {xxx} should b a block
        return node
    else:
        lexer.pop()
        lit = LiteralNode(token.text, token.token_type.capitalize())
        lit.start_pos = token.start_pos
        lit.end_pos = token.end_pos
        return lit


def parse_identifier(lexer: Lexer):
    token = lexer.expect_pop("id", "self")
    id = IdNode(token.text)
    id.start_pos = token.start_pos
    id.end_pos = token.end_pos
    return id

def parse_var(lexer: Lexer):
    return VarNode(parse_identifier(lexer))

def parse_type(lexer: Lexer):
    if lexer.try_peek("("):
        return parse_function_type(lexer)
    token = lexer.expect_pop("id")
    type_node = TypeNode(token.text)
    type_node.start_pos = token.start_pos
    type_node.end_pos = token.end_pos
    return type_node


def parse_trait_constraint(lexer: Lexer):
    lexer.expect_pop("impl")
    if lexer.try_peek("("):
        lexer.pop()
        traits = RepeatParser("+", ")").parse(lexer, parse_trait)
    else:
        traits = [parse_trait(lexer)]
    return TraitConstraintNode(traits)


def parse_function_arg_type(lexer: Lexer):
    if lexer.try_peek("impl"):
        return parse_trait_constraint(lexer)
    return parse_type(lexer)



def parse_rel(lexer: Lexer):
    left = parse_add(lexer)
    while True:
        if lexer.peek().token_type not in ('>', '<', '>=', '<='):
            break
        node = BinaryOpNode(lexer.peek().token_type)
        lexer.pop()
        right = parse_add(lexer)
        node.left = left
        node.right = right
        left = node
    return left

def parse_eq(lexer: Lexer):
    left = parse_rel(lexer)
    while True:
        if lexer.peek().token_type not in ('==', '!='):
            break
        node = BinaryOpNode(lexer.peek().token_type)
        lexer.pop()
        right = parse_rel(lexer)
        node.left = left
        node.right = right
        left = node
    return left

def parse_and(lexer: Lexer):
    left = parse_eq(lexer)
    while True:
        if lexer.peek().token_type != 'and':
            break
        node = BinaryOpNode(lexer.peek().token_type)
        lexer.pop()
        right = parse_eq(lexer)
        node.left = left
        node.right = right
        left = node
    return left

def parse_or(lexer: Lexer) -> ASTNode:
    left = parse_and(lexer)
    while True:
        if lexer.peek().token_type != 'or':
            break
        node = BinaryOpNode(lexer.peek().token_type)
        lexer.pop()
        right = parse_and(lexer)
        node.left = left
        node.right = right
        left = node
    return left


def parse_add(lexer: Lexer) -> Optional[ASTNode]:
    left = parse_mul(lexer)
    while True:
        if lexer.peek().token_type not in ('+', '-'):
            break
        node = BinaryOpNode(lexer.peek().text)
        lexer.pop()
        right = parse_mul(lexer)
        node.left = left
        node.right = right
        left = node
    return left

def parse_attr(lexer: Lexer) -> Optional[ASTNode]:
    left = parse_expr_unit(lexer)
    while True:
        if lexer.peek().token_type not in ('.', '[', '('):
            break
        if lexer.try_peek("."):
            lexer.pop()
            node = AttributeNode(left, parse_identifier(lexer))
            left = node
        elif lexer.try_peek("("):
            lexer.pop()
            node = FunctionCallNode(left, RepeatParser(",", ")").parse(lexer, parse_expr))
            left = node
    return left

def parse_mul(lexer: Lexer) -> Optional[ASTNode]:
    left = parse_attr(lexer)
    while True:
        if lexer.peek().token_type not in ('*', '/'):
            break
        node = BinaryOpNode(lexer.peek().token_type)
        lexer.pop()
        right = parse_attr(lexer)
        node.left = left
        node.right = right
        left = node
    return left

def parse_properties(lexer: Lexer):
    data = parse_identifier(lexer)

    lexer.expect_pop(".")
    prop_name = parse_identifier(lexer)
    data = AttributeNode(data, prop_name)
    return data

def parse_expr(lexer: Lexer) -> Optional[ASTNode]:
    return parse_or(lexer)

def parse_assign(lexer: Lexer) -> AssignNode:
    var = parse_var(lexer)
    lexer.expect_pop("=")
    expr = parse_expr(lexer)
    return AssignNode(var, expr)

def parse_return(lexer: Lexer) -> ASTNode:
    lexer.expect_pop("return")
    return ReturnNode(parse_expr(lexer))

def parse_function_type(lexer: Lexer) -> FunctionTypeNode:
    lexer.expect_pop("(")
    arg_types = RepeatParser(",", ")").parse(lexer, parse_type)
    lexer.expect_pop("->")
    return_type = parse_type(lexer)
    return FunctionTypeNode(arg_types, return_type)



def parse_stmt(lexer: Lexer, inside_function=False) -> Optional[ASTNode]:
    match lexer.peek().token_type:
        case "if":
            node = parse_if_stmt(lexer)
        case "while":
            node = parse_while_stmt(lexer)
        case "id":
            lexer.pop()
            if lexer.peek().token_type == '=':
                lexer.unpop()
                node = parse_assign(lexer)
            else:
                lexer.unpop()
                node = parse_expr(lexer)
            lexer.expect_pop(";")
        case "def":
            node = parse_func_def(lexer)
        case "let":
            node = parse_var_def(lexer)
            lexer.expect_pop(";")
        case "return":
            node = parse_return(lexer)
            lexer.expect_pop(";")
        case _:
            return None
    return node

def parse_block(lexer: Lexer, inside_function=False) -> Optional[BlockNode]:
    lexer.expect_pop("{")
    node = BlockNode([])
    if lexer.try_peek("}"):
        lexer.pop()
        return node
    while True:
        node.stmts.append(parse_stmt(lexer, inside_function))
        if lexer.try_peek("}"):
            lexer.pop()
            break
    return node

def parse_if_stmt(lexer: Lexer) -> Optional[IfStatement]:
    lexer.expect_pop("if")
    condition_node = parse_expr(lexer)
    body_node = parse_block(lexer)
    branches = [(condition_node, body_node)]
    else_branches = None
    while True:
        if lexer.try_peek("elif"):
            lexer.pop()
            condition_node = parse_expr(lexer)
            body_node = parse_block(lexer)
            branches.append((condition_node, body_node))
        elif lexer.try_peek("else"):
            lexer.pop()
            else_branches = parse_block(lexer)
        else:
            break
    return IfStatement(branches, else_branches)

def parse_while_stmt(lexer: Lexer) -> Optional[LoopStatement]:
    lexer.expect_pop("while")
    condition_node = parse_expr(lexer)
    body_node = parse_block(lexer)
    return LoopStatement(condition_node, body_node)

def parse_func_def(lexer: Lexer, trait_node: TraitImplNode=None) -> FuncDefNode:
    lexer.expect_pop("def")
    function_name = parse_identifier(lexer)
    lexer.expect_pop("(")
    args = RepeatParser(",", ")").parse(lexer, combiner(parse_identifier, drop(":"), parse_function_arg_type))
    lexer.expect_pop("->")
    return_type = parse_function_arg_type(lexer)
    body = parse_block(lexer, True)
    return FuncDefNode(function_name, [VarDefNode(id, type) for id, type in args], body, return_type, trait_node)

def parse_var_def(lexer: Lexer):
    lexer.expect_pop("let")
    id_node = parse_identifier(lexer)
    type_node = None
    init_node = None
    if lexer.try_peek(":"):
        lexer.pop()
        type_node = parse_function_type(lexer) if lexer.try_peek("(") else parse_type(lexer)
        if lexer.try_peek(";"):
            return VarDefNode(id_node, type_node, None)
    # let a = 1; will infer type
    if lexer.try_peek("="):
        lexer.pop()
        init_node = parse_or(lexer)
    return VarDefNode(id_node, type_node, init_node)

def parse_type_def(lexer: Lexer) -> TypeDefNode:
    lexer.expect_pop("type")
    type_name = parse_identifier(lexer)
    lexer.expect_pop("=")
    lexer.expect_pop("{")
    type_def = RepeatParser(",", "}").parse(lexer, combiner(parse_identifier, drop(":"), parse_type))
    return TypeDefNode(type_name, type_def)

def parse_trait(lexer: Lexer) -> TraitNode:
    id = parse_identifier(lexer)
    trait_node = TraitNode(id)
    trait_node.start_pos = id.start_pos
    trait_node.end_pos = id.end_pos
    return trait_node

def parse_trait_def(lexer: Lexer) -> TraitDefNode:
    lexer.expect_pop("trait")
    trait_name = parse_identifier(lexer)
    lexer.expect_pop("(")
    type_var = parse_type(lexer)
    lexer.expect_pop(")")
    lexer.expect_pop("{")

    traits = []
    while True:
        if lexer.try_peek("}"):
            lexer.pop()
            break
        lexer.expect_pop("def")
        function_name = parse_identifier(lexer)
        lexer.expect_pop("(")
        args = RepeatParser(",", ")").parse(lexer, combiner(parse_identifier, drop(":"), parse_type))
        lexer.expect_pop("->")
        return_type = parse_type(lexer)
        trait_func = TraitFunctionNode(function_name, [VarDefNode(id, type) for id, type in args], return_type)
        traits.append(trait_func)
    return TraitDefNode(trait_name, type_var, traits)

def parse_trait_impl(lexer: Lexer) -> TraitImplNode:
    lexer.expect_pop("impl")
    trait = parse_trait(lexer)
    lexer.expect_pop("for")
    type_node = parse_type(lexer)
    lexer.expect_pop("{")
    impls: List[FuncDefNode] = []
    while True:
        if lexer.try_peek("}"):
            lexer.pop()
            break
        trait_func = parse_func_def(lexer, trait.name.name)
        impls.append(trait_func)
    trait_node = TraitImplNode(trait, type_node, impls)
    for impl in impls:
        impl.trait_node = trait_node
    return trait_node

def parse_proc(lexer: Lexer) -> ProcNode:
    proc_node = ProcNode()
    while True:
        match lexer.peek().token_type:
            case "type":
                node = parse_type_def(lexer)
            case "trait":
                node = parse_trait_def(lexer)
            case "impl":
                node = parse_trait_impl(lexer)
            case Lexer.EOF.token_type:
                break
            case _:
               node = parse_stmt(lexer)
        proc_node.children.append(node)
    return proc_node