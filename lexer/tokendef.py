from dataclasses import dataclass
from lexer.re_expression import Expression


@dataclass
class TokenDef:
    name: str
    index: int
    exp: Expression
    tag: str

    def __str__(self):
        return f"Token(index={self.index}, name={self.name}, tag={self.tag})"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other: 'TokenDef'):
        return self.name == other.name


class TokenFactory:

    def __init__(self):
        self.index = 0
        self.token_mapping = {}

    def create(self, exp: Expression, name: str, tag: str = None):
        token = TokenDef(name, self.index, exp, tag)
        self.token_mapping[self.index] = token
        self.index += 1
        return token

    def create_by_string(self, string: str, tag: str = None):
        return self.create(
            Expression.string(string),
            string,
            tag=tag
        )

    def get(self, index: int):
        return self.token_mapping[index]

    def tokens(self):
        return self.token_mapping.values()


@dataclass
class Token:
    token_type: str
    text: str
    position: (int, int)


EOF = Token(
        "__EOF__",
        "",
        None
)
