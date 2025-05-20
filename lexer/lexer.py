from lexer.tokendef import TokenDef, Token, EOF as EOF_TOKEN, TokenFactory
from lexer.state import DFAState
from lexer.utils import nfa_to_dfa
from typing import List, Dict, Optional, Union, Set
from lexer.re_expression import OrExpression
from lexer.range import CharRange
from collections import defaultdict
from lexer.range import RangeSearch
from abc import ABC, abstractproperty, abstractmethod
from error.exception import SyntaxError
from error.reporter import SourceCodeMaker

class CharStream:

    EOF = -1

    def peek(self) -> int: pass

    def pop(self) -> int: pass


class SimpleCharSteam(CharStream):

    def __init__(self, string: str):
        self.string = list(string)
        self.current_index = 0
        self.rows = string.split("\n")

    def peek(self):
        if self.current_index == len(self.string):
            return CharStream.EOF
        return ord(self.string[self.current_index])

    def pop(self):
        res = self.peek()
        if res == CharStream.EOF:
            return CharStream.EOF
        self.current_index += 1
        return res

    def peek_line(self, row):
        return self.rows[row]


class IndexAssigner:

    def __init__(self, start_index):
        self.current_index = start_index - 1
        self.index_mapping = {}

    def assign_index(self, dfa_state: DFAState):
        ind = self.index_mapping.get(dfa_state)
        if ind is not None:
            return ind
        ind = self.current_index + 1
        self.current_index = ind
        self.index_mapping[dfa_state] = ind
        return ind


class StateTable:

    INIT_STATE = 1
    STOP_STATE = 0

    def __init__(self, dfa_init_state: DFAState):
        self._dfa_init_state = dfa_init_state
        self._trans_table, self._accept_table = StateTable.get_trans_table(dfa_init_state)
        self._trans_searches: Dict[int, RangeSearch] = {state: RangeSearch(list(trans.keys())) for state, trans in self._trans_table.items()}
        self._current_state_index: int = StateTable.INIT_STATE
        self._stop = False

    def trans(self, input_char: int) -> Optional[int]:
        state_index = self._current_state_index
        if state_index not in self._trans_searches:
            self._stop = True
            return None
        # 使用二分查找判断该输入会转移到哪个状态
        r = self._trans_searches.get(state_index).search_cover(CharRange.index(input_char))
        if not r:
            self._stop = True
            return None
        self._current_state_index = self._trans_table[state_index][r]
        return self._current_state_index

    def get_accept(self) -> TokenDef:
        return self._accept_table.get(self._current_state_index)

    @classmethod
    def get_trans_table(cls, init_state: DFAState):
        transaction_table = defaultdict(dict)
        pending_states = [init_state]
        index_assigner = IndexAssigner(cls.INIT_STATE)
        accept_table = {}
        while pending_states:
            state = pending_states.pop(0)
            # 获取当前 state 的 index
            state_index = index_assigner.assign_index(state)
            # 如果是可接受状态
            if state.accept_as:
                accept_table[state_index] = state.accept_as
            if state_index not in transaction_table:
                for edge in state.edges:
                    next_state = edge.state
                    next_state_index = index_assigner.assign_index(next_state)
                    transaction_table[state_index][edge.char] = next_state_index
                    pending_states.append(next_state)
        return transaction_table, accept_table

    def init(self):
        self._current_state_index = self.INIT_STATE
        self._stop = False


class Lexer(ABC):

    EOF = EOF_TOKEN

    @abstractmethod
    def pop(self) -> Token: pass

    @abstractmethod
    def peek(self) -> Token: pass

    def expect(self, *args, pop=False):
        if self.peek().token_type in args:
            res = self.peek()
            if pop:
                self.pop()
            return res
        else:
            raise SyntaxError(f"expect token in {args}, but got {self.peek().token_type}")

    def expect_pop(self, *args):
        return self.expect(*args, pop=True)

    def try_peek(self, token_type):
        if self.peek().token_type == token_type:
            return self.peek()
        return None

    @abstractmethod
    def unpop(self) -> Token: pass


class MockLexer(Lexer):

    def __init__(self, tokens):
        self._token_index = 0
        self._tokens = tokens

    def peek(self) -> Token:
        if self._token_index == len(self._tokens):
            raise IndexError("already read all tokens")
        return self._tokens[self._token_index]

    def pop(self) -> Token:
        res = self._tokens[self._token_index]
        self._token_index += 1
        return res

    def unpop(self):
        self._token_index -= 1
        return self._tokens[self._token_index]



class BaseLexer(Lexer):

    def __init__(self, tokens: TokenFactory, line_marker: SourceCodeMaker, chars: Union[CharStream, str], ignore: Set[str]=None):
        super().__init__()
        self._token_def = tokens
        self._current_token_detail: Optional[Token] = None
        self._current_token: Optional[TokenDef] = None
        self._exp = self._create_exp(tokens.tokens())
        self._dfa = nfa_to_dfa(self._exp.to_nfa())
        self._state_table = StateTable(self._dfa)
        self._current_text = ""
        self._chars = SimpleCharSteam(chars) if type(chars) is str else chars
        self._col = 1
        self._start_col = 1
        self._ignore = ignore
        self.row = 1
        self._start_row = 1
        self._mock_lexer = MockLexer(self._parse_all())
        self._line_marker = line_marker


    def _create_exp(self, tokens):
        expressions = []
        for token in tokens:
            token.exp.accept_as = token
            expressions.append(token.exp)
        return OrExpression(expressions)

    def peek(self) -> Token:
        return self._mock_lexer.peek()

    def pop(self) -> Token:
        return self._mock_lexer.pop()

    def unpop(self) -> Token:
        return self._mock_lexer.unpop()

    def init(self):
        self._current_token = None
        self._current_text = ""
        self._state_table.init()
        self._start_col = self._col
        self._start_row = self.row

    def _parse_all(self) -> List[Token]:
        res = []
        while (token := self._parse_token()) != Lexer.EOF:
            if token.token_type not in self._ignore:
                res.append(token)
        res.append(Lexer.EOF)
        return res

    def _parse_token(self) -> Token:
        state = StateTable.INIT_STATE
        while True:
            accept_token = self._state_table.get_accept()
            if accept_token:
                self._current_token = accept_token
            c = self._chars.peek()
            next_state = self._state_table.trans(c)
            if not next_state:
                if self._current_token:
                    if self._current_text == '\n':
                        self.row += 1
                        self._col = 1
                    self._current_token_detail = Token(self._current_token.name,
                                                       text=self._current_text,
                                                       start_pos=(self._start_row, self._start_col),
                                                       end_pos=(self.row, self._col - 1)
                                                       )
                    res = self._current_token_detail
                    self.init()
                    return res
                if c == CharStream.EOF:
                    return EOF_TOKEN
                if state == StateTable.INIT_STATE:
                    raise Exception(f"unknown input {chr(c)}")
                self.init()
            else:
                self._current_text += chr(c)
                self._chars.pop()
                self._col += 1

    def expect(self, *args, pop=False):
        if self.peek().token_type in args:
            res = self.peek()
            if pop:
                self.pop()
            return res
        else:
            token = self.peek()
            if token == Lexer.EOF:
                previous_token = self.unpop()
                raise SyntaxError(f"unexpected EOF after\n" + self._line_marker.mark(previous_token.start_pos, previous_token.end_pos))
            expect_token = " ".join([f"'{x}'" for x in args])
            raise SyntaxError(f"expect token in {expect_token}, but got '{self.peek().token_type}'\n" + self._line_marker.mark(token.start_pos, token.end_pos))

    def expect_pop(self, *args):
        return self.expect(*args, pop=True)