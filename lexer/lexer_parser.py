from lexer.token import Token
from lexer.state import DFAState
from lexer.utils import nfa_to_dfa
from typing import List, Dict, Optional
from lexer.re_expression import OrExpression
from lexer.range import CharRange
from collections import defaultdict
from lexer.range import RangeSearch


class CharStream:

    EOF = -1

    def peek(self) -> int: pass

    def pop(self) -> int: pass


class SimpleCharSteam(CharStream):

    def __init__(self, string: str):
        self.string = list(string)
        self.current_index = 0

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


class IndexAssigner:

    def __init__(self):
        self.current_index = 0
        self.index_mapping = {}

    def assign_index(self, dfa_state: DFAState):
        ind = self.index_mapping.get(dfa_state)
        if ind is not None:
            return ind
        ind = self.current_index + 1
        self.current_index = ind
        self.index_mapping[dfa_state] = ind
        return ind


def get_trans_table(init_state: DFAState):
    transaction_table = defaultdict(dict)
    pending_states = [init_state]
    index_assigner = IndexAssigner()
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


class StateTable:

    def __init__(self, dfa_init_state: DFAState):
        self._dfa_init_state = dfa_init_state
        self._trans_table, self._accept_table = get_trans_table(dfa_init_state)
        self._trans_searches: Dict[int, RangeSearch] = {state: RangeSearch(list(trans.keys())) for state, trans in self._trans_table.items()}

    def trans(self, state_index, input_char: str) -> Optional[int]:
        if state_index not in self._trans_searches:
            return None
        r = self._trans_searches.get(state_index).search_cover(CharRange.char(input_char))
        if not r:
            return None
        return self._trans_table[state_index][r]

    def get_accept(self, state_index: int):
        return self._accept_table.get(state_index)


class Lexer:

    def parse(self, tokens: List[Token], chars: CharStream):
        expressions = []
        for token in tokens:
            token.exp.accept_as = token
            expressions.append(token.exp)
        exp = OrExpression(expressions)
        nfa_state = exp.to_nfa()
        dfa = nfa_to_dfa(nfa_state)
        state_table = StateTable(dfa)
        state = 1
        text = ""
        while True:
            c = chars.peek()
            last_accept_token = state_table.get_accept(state)
            if c == CharStream.EOF:
                if not last_accept_token:
                    raise Exception(f"unknown EOF")
                else:
                    print(text, last_accept_token)
                    return
            next_state = state_table.trans(state, c)

            if not next_state:
                if last_accept_token:
                    print(text, last_accept_token)
                    text = ""
                if c == CharStream.EOF:
                    return
                if state == 1:
                    raise Exception(f"unknown input {c}")
                state = 1
            else:
                text += c
                chars.pop()
                state = next_state
