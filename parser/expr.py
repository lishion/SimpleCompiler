from parse.node import ASTNode, BinaryOpNode, LiteralNode, StmtNode
from lexer.lexer_parse import Lexer
from typing import Optional


def parse_id(lexer: Lexer):
    if lexer.peek() == Lexer.EOF:
        return None
    if lexer.peek().name == "(":
        lexer.pop()
        res = parse_add(lexer)
        lexer.expect(")")
        lexer.pop()
        return res
    lexer.expect('float', 'int', 'lit', 'id')
    token = lexer.pop()
    return LiteralNode(token.text, token.name)

def parse_rel(lexer: Lexer):
    left = parse_add(lexer)
    if not left:
        return None
    while True:
        if lexer.peek().name not in ('>', '<', '>=', '<='):
            break
        node = BinaryOpNode(lexer.peek().name)
        lexer.pop()
        right = parse_add(lexer)
        node.children.append(left)
        node.children.append(right)
        left = node
    return left

def parse_eq(lexer: Lexer):
    left = parse_rel(lexer)
    if not left:
        return None
    while True:
        if lexer.peek().name not in ('==', '!='):
            break
        node = BinaryOpNode(lexer.peek().name)
        lexer.pop()
        right = parse_rel(lexer)
        node.children.append(left)
        node.children.append(right)
        left = node
    return left

def parse_and(lexer: Lexer):
    left = parse_eq(lexer)
    if not left:
        return None
    while True:
        if lexer.peek().name != 'and':
            break
        node = BinaryOpNode(lexer.peek().name)
        lexer.pop()
        right = parse_eq(lexer)
        node.children.append(left)
        node.children.append(right)
        left = node
    return left

def parse_or(lexer: Lexer):
    left = parse_and(lexer)
    if not left:
        return None
    while True:
        if lexer.peek().name != 'or':
            break
        node = BinaryOpNode(lexer.peek().name)
        lexer.pop()
        right = parse_and(lexer)
        node.children.append(left)
        node.children.append(right)
        left = node
    return left


def parse_add(lexer: Lexer) -> Optional[ASTNode]:
    left = parse_mul(lexer)
    if not left:
        return None
    while True:
        if lexer.peek().name not in ('+', '-'):
            break
        node = BinaryOpNode(lexer.peek().name)
        lexer.pop()
        right = parse_mul(lexer)
        node.children.append(left)
        node.children.append(right)
        left = node
    return left


def parse_mul(lexer: Lexer) -> Optional[ASTNode]:
    left = parse_id(lexer)
    if not left:
        return None
    while True:
        if lexer.peek().name not in ('*', '/'):
            break
        node = BinaryOpNode(lexer.peek().name)
        lexer.pop()
        right = parse_id(lexer)
        node.children.append(left)
        node.children.append(right)
        left = node
    return left

def parse_expr(lexer: Lexer) -> Optional[ASTNode]:
    token = parse_or(lexer)
    if not token:
        return None
    if lexer.peek().name == "=":
        op = BinaryOpNode("=")
        lexer.pop()
        right = parse_or(lexer)
        op.children.append(token)
        op.children.append(right)
        return op
    return token


def parse_stmt(lexer: Lexer) -> Optional[ASTNode]:
    node = StmtNode("stmt")
    while (exp := parse_expr(lexer)) is not None:
        lexer.expect(";")
        lexer.pop()
        node.children.append(exp)
    return node

