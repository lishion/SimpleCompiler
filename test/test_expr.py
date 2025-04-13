from unittest import TestCase
from parser.expr import parse_mul, parse_add, parse_expr, parse_stmt
from lexer.lexer_parser import MockLexer, BaseLexer
from grammer import TOKENS
from parser.node import IDS

class Test(TestCase):
    def test_parse_mul(self):
        lexer = BaseLexer(TOKENS, 'a=1==1 and 1==2;a;', ignore="white_space")
        left = parse_stmt(lexer)
        left.walk()
        print(left.eval())
        print(IDS)

