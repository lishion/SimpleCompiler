from unittest import TestCase
from parser.expr import parse_stmt, parse_proc
from lexer.lexer import BaseLexer
from grammer import TOKENS
# from parser.node import IDS
from pprint import pprint

from parser.visitor import PrintVisitor


class Test(TestCase):

    def test_parse(self, code):
        lexer = BaseLexer(TOKENS, code, ignore="white_space")
        return parse_proc(lexer)

    def test_parse_mul(self):
        # lexer = BaseLexer(TOKENS, '[1, 2, 3, 4+5, 3==1];', ignore="white_space")
        # left = parse_stmt(lexer)
        # left.walk()
        # print(left.eval())
        # print(IDS)
        #
        # lexer = BaseLexer(TOKENS, '{1: 2, "3": 4, 1+4: 5+6};', ignore="white_space")
        # left = parse_stmt(lexer)
        # left.walk()
        # print(left.eval())
        # print(IDS)
        #
        # lexer = BaseLexer(TOKENS, 'a={1: 2, "3": 4, 1+4: 5+6}; print(a);', ignore="white_space")
        # left = parse_stmt(lexer)
        # left.walk()
        # print(left.eval())
        # print(IDS)

        self.test_parse("""
        if 2 == 2{
            print("true");
        } 
            print("true");
        }
        else{
            print("false");
        }
        """).eval()
        # print(left.eval())
        # print(IDS)

    def test_parse_while(self):
        self.test_parse(
            """
            while()
            """
        )

    def test_parse_func(self):
        node = self.test_parse("""
            def hello(name, dd){
                a = name + 2;
                b = a + dd;
            }
            a = hello(2, 1);
            print(a);
            a = 1;
            b = 2;
            if a >= 1{
                print("hello");
            }
            if b < 0{
                print("world");
            }
        """)
        print(node)
        print(node.eval())