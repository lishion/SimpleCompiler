from unittest import TestCase
from lexer.re_expression import *
from lexer.tokendef import TokenFactory, EOF
from lexer.lexer import BaseLexer, SimpleCharSteam
from grammer import TOKENS

class TestCharRange(TestCase):
    def test_char(self):
        tokenDef = TokenFactory()
        #
        # [tokenDef.create_by_string(c) for c in "+-*/=;><"]
        # tokenDef.create_by_string("let")
        # tokenDef.create(
        #     (
        #             Expression.range("a", "z")
        #             | Expression.range("A", "Z")
        #             | Expression.char("_")
        #     )
        #     + (
        #             Expression.range("a", "z")
        #             | Expression.range("A", "Z")
        #             | Expression.range("0", "9")
        #             | Expression.char("_")
        #     ),
        #     "Identifier"
        # )
        tokenDef.create(
            Expression.concat(
                Expression.char('"'),
                (
                      Expression.any_char(['"', '\\'])
                    | Expression.string(r'\"')
                 ).any(),
                Expression.char('"')
            ),
            "lit"
        )
        # #
        # tokenDef.create(
        #     Expression.range('0', '9').many(),
        #     "int")
        #
        # tokenDef.create(
        #     Expression.range('0', '9').many() + Expression.char(".") + Expression.range('0', '9').many(),
        #     "float")
        #
        tokenDef.create(
            Expression.one_of(
                "\t",
                "\n",
                "\r",
                " "
            ),
            "white_space"
        )

        # tokenDef.create(Expression.char("a") + (Expression.char(".") + Expression.char("b")).optional(), "ab")

        lexer = BaseLexer(tokenDef, SimpleCharSteam(r'"123\"" "333"'))



        while lexer.peek() != EOF:
            print(lexer.pop().text)

    def test_position(self):
        code = """
let let;
def test(a: String): String{
              return a;
           }
           def test(b: Int): Int{
              return b;
           }
           print(a123);
           print(test("1"));
        """
        lexer = BaseLexer(TOKENS, code, ignore="white_space")
        while lexer.peek() != EOF:
            print(lexer.pop())