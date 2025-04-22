
from lexer.re_expression import *
from lexer.tokendef import TokenFactory


TOKENS = TokenFactory()

[TOKENS.create_by_string(c) for c in "+-*/=;()<>{}[],:"]
TOKENS.create_by_string(">=")
TOKENS.create_by_string("<=")
TOKENS.create_by_string("==")
TOKENS.create_by_string("!=")
TOKENS.create_by_string("let")
TOKENS.create_by_string("and")
TOKENS.create_by_string("or")
TOKENS.create_by_string("if")
TOKENS.create_by_string("else")
TOKENS.create_by_string("elif")
TOKENS.create_by_string("for")
TOKENS.create_by_string("while")
TOKENS.create_by_string("def")
TOKENS.create(
    (
            Expression.range("a", "z")
            | Expression.range("A", "Z")
            | Expression.char("_")
    )
    + (
            Expression.range("a", "z")
            | Expression.range("A", "Z")
            | Expression.range("0", "9")
            | Expression.char("_")
    ).any(),
    "id"
)
TOKENS.create(
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
#
TOKENS.create(
    Expression.range('0', '9').many(),
    "int")

TOKENS.create(
    Expression.range('0', '9').many() + Expression.char(".") + Expression.range('0', '9').many(),
    "float")


TOKENS.create(
    Expression.one_of(
        "\t",
        "\n",
        "\r",
        " "
    ),
    "white_space"
)

