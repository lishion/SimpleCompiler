from lexer.re_expression import *
from lexer.token import Token, TokenDef
from lexer.lexer_parser import Lexer, SimpleCharSteam
from lexer.utils import dis_join

if __name__ == '__main__':
    tokenDef = TokenDef()
    tokenDef.create(
        Expression.range('a', 'z'),
        "id"
    )
    # tokenDef.create(
    #     Expression.string("let"),
    #     "let"
    # )
    # [tokenDef.create_by_string(c) for c in "+-*/="]
    # tokenDef.create(
    #     Expression.Or(
    #         Expression.range("a", "z"),
    #         Expression.range("A", "Z"),
    #         Expression.range("0", "9"),
    #         Expression.char("_"),
    #     ).many(),
    #     "id"
    # )
    #
    # tokenDef.create(Expression.range('0', '9').many(), "number")
    #
    # tokenDef.create(
    #     Expression.string("public"),
    #     "public"
    # )
    #
    #
    #
    # tokenDef.create(
    #     Expression.one_of(
    #         "\t",
    #         "\n",
    #         "\r",
    #         " "
    #     ),
    #     "white_space"
    # )

    lexer = Lexer()
    lexer.parse(tokenDef.tokens(), SimpleCharSteam("let a=1 b12321312=1"))
