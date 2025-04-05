from unittest import TestCase
from lexer.re_expression import *
from lexer.token import TokenDef
from lexer.lexer_parser import Lexer, SimpleCharSteam


class TestCharRange(TestCase):
    def test_char(self):
        tokenDef = TokenDef()
        # tokenDef.create(Expression.range("a", "z").many(), "token")
        # tokenDef.create(Expression.range("a", "z").many(), "token")

        [tokenDef.create_by_string(c) for c in "+-*/=;"]
        tokenDef.create(
            Expression.concat(
                Expression.Or(
                    Expression.range("a", "z"),
                    Expression.range("A", "Z"),
                    Expression.char("_"),
                ),
                Expression.Or(
                    Expression.range("a", "z"),
                    Expression.range("A", "Z"),
                    Expression.range("0", "9"),
                    Expression.char("_"),
                ).any(),
            ),
            "id"
        )
        tokenDef.create(
            Expression.concat(
                Expression.char('"'),
                Expression.any_char('"').any(),
                Expression.char('"')
            ),
            "lit"
        )
        #
        tokenDef.create(Expression.range('0', '9').many(), "number")
        #
        # tokenDef.create(
        #     Expression.string("public"),
        #     "public"
        # )
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

        lexer = Lexer()
        lexer.parse(tokenDef.tokens(), SimpleCharSteam('let a= "1";let b = 21231231'))

