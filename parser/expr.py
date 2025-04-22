from lexer.tokendef import Token
from parser.node import ASTNode, BinaryOpNode, LiteralNode, BlockNode, FunctionCallNode, VarNode, IndexNode, \
    LitArrayNode, LitDictNode, IfStatement, LoopStatement, FuncDefStatement, ProcNode, AssignNode
from lexer.lexer import Lexer
from typing import Optional


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

def parse_id(lexer: Lexer):
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
    lexer.expect('float', 'int', 'lit', 'id')
    token = lexer.pop()
    if token.token_type == "id":
        if lexer.peek().token_type == "(":
            lexer.pop()
            node = FunctionCallNode(token.text)
            while True:
                if lexer.peek().token_type == ")":
                    lexer.pop()
                    break
                node.args.append(parse_expr(lexer))
                if lexer.try_peek(","):
                    lexer.pop()
                elif lexer.try_peek(")"):
                    lexer.pop()
                    break
            return node
        if lexer.peek().token_type == "[":
            lexer.pop()
            return parse_index(token, lexer)
        else:
            return VarNode(token.text)
    return LiteralNode(token.text)

def parse_rel(lexer: Lexer):
    left = parse_add(lexer)
    if not left:
        return None
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
    if not left:
        return None
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
    if not left:
        return None
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
    if not left:
        return None
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
    if not left:
        return None
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


def parse_mul(lexer: Lexer) -> Optional[ASTNode]:
    left = parse_id(lexer)
    if not left:
        return None
    while True:
        if lexer.peek().token_type not in ('*', '/'):
            break
        node = BinaryOpNode(lexer.peek().token_type)
        lexer.pop()
        right = parse_id(lexer)
        node.left = left
        node.right = right
        left = node
    return left

def parse_expr(lexer: Lexer) -> Optional[ASTNode]:
    expr_node = parse_or(lexer)
    if not expr_node:
        return None
    if lexer.peek().token_type == "=":
        op = AssignNode()
        lexer.pop()
        right = parse_or(lexer)
        op.left = expr_node
        op.right = right
        return op
    return expr_node


def parse_stmt(lexer: Lexer) -> Optional[ASTNode]:
    node = BlockNode([])
    while (exp := parse_expr(lexer)) is not None:
        lexer.expect_pop(";")
        node.stmts.append(exp)
    return node

def parse_block(lexer: Lexer) -> Optional[BlockNode]:
    lexer.expect_pop("{")
    node = BlockNode([])
    while (exp := parse_expr(lexer)) is not None:
        lexer.expect_pop(";")
        node.stmts.append(exp)
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

def parse_func_def(lexer: Lexer) -> FuncDefStatement:
    lexer.expect_pop("def")
    function_name = lexer.expect_pop("id").text
    lexer.expect_pop("(")
    args = []
    while True:
        if lexer.try_peek(")"):
            lexer.pop()
            break
        arg = lexer.expect_pop("id")
        args.append(arg.text)
        if lexer.try_peek(","):
            lexer.pop()
        if lexer.try_peek(")"):
            lexer.pop()
            break
    body = parse_block(lexer)
    return FuncDefStatement(function_name, args, body)

def parse_proc(lexer: Lexer):
    proc_node = ProcNode()
    while True:
        if lexer.try_peek("if"):
            node = parse_if_stmt(lexer)
        elif lexer.try_peek("while"):
            node = parse_while_stmt(lexer)
        elif lexer.try_peek("id"):
            node = parse_expr(lexer)
            lexer.expect_pop(";")
        elif lexer.try_peek("def"):
            node = parse_func_def(lexer)
        elif lexer.try_peek(Lexer.EOF.token_type):
            break
        else:
            continue
        proc_node.children.append(node)
    return proc_node
