from abc import abstractmethod
from lexer.state import Edge, NFAState, NFA, CharRange, AnyStr
from typing import List, Optional
from lexer.utils import split_range_by
import sys


class Expression:

    def __init__(self, accept_as: Optional = None):
        self.accept_as = accept_as

    def to_nfa(self) -> NFA:
        nfa = self.exp_to_nfa()
        nfa.end_state.accept_as = self.accept_as
        return nfa

    @abstractmethod
    def exp_to_nfa(self) -> NFA: pass

    @staticmethod
    def char(ch: str) -> 'Expression':
        return CharExpression(ch)

    @staticmethod
    def empty():
        return EmptyExpression()

    def optional(self):
        return OrExpression([self, Expression.empty()])

    def star(self):
        return StarExpression(self)

    def any(self):
        return self.star()

    @staticmethod
    def string(string):
        return ConcatExpression([Expression.char(c) for c in string])

    @staticmethod
    def one_of(*chrs):
        return OrExpression([Expression.char(c) for c in chrs])

    @staticmethod
    def range(start, end):
        return RangeExpression(ord(start), ord(end))

    @staticmethod
    def Or(*exps):
        return OrExpression(list(exps))

    def many(self):
        return Expression.concat(self, self.star())

    @staticmethod
    def concat(*exps):
        return ConcatExpression(list(exps))

    @staticmethod
    def any_char(except_chars: List[AnyStr]=None):
        ranges = split_range_by(0, sys.maxunicode, except_chars or [])
        return OrExpression([Expression.range(chr(s), chr(e)) for s, e in ranges])

    def __add__(self, other: 'Expression'):
        return ConcatExpression([self, other])

    def __or__(self, other):
        return OrExpression([self, other])


class RangeExpression(Expression):

    def __init__(self, start, end):
        super().__init__()
        self._start = start
        self._end = end

    def exp_to_nfa(self) -> NFA:
        end_state = NFAState()
        entry = Edge(CharRange(self._start, self._end), end_state)
        return NFA(entry, end_state)


class CharExpression(RangeExpression):

    def __init__(self, accept: str):
        super().__init__(ord(accept), ord(accept))


class EmptyExpression(Expression):

    def __init__(self):
        super().__init__()

    def exp_to_nfa(self) -> NFA:
        end_state = NFAState()
        entry = Edge.empty(end_state)
        return NFA(entry, end_state)


class OrExpression(Expression):

    def __init__(self, expressions: List[Expression]):
        super().__init__()
        self.expressions = expressions

    def exp_to_nfa(self) -> NFA:
        entry_state = NFAState()
        entry = Edge.empty(entry_state)
        end_state = NFAState()
        for exp in self.expressions:
            nfa = exp.to_nfa()
            nfa.end_state.add_edge(Edge.empty(end_state))
            entry_state.add_edge(nfa.entry_edge)
        return NFA(entry, end_state)


class ConcatExpression(Expression):
    def __init__(self, expressions: List[Expression]):
        super().__init__()
        self.expressions = expressions

    def exp_to_nfa(self) -> NFA:
        entry_state = NFAState()
        entry = Edge.empty(entry_state)
        state = entry_state
        for exp in self.expressions:
            nfa = exp.to_nfa()
            state.add_edge(nfa.entry_edge)
            state = nfa.end_state
        return NFA(entry, state)


class StarExpression(Expression):

    def __init__(self, expression: Expression):
        super().__init__()
        self.expression = expression

    def exp_to_nfa(self) -> NFA:
        entry_state = NFAState()

        end_state = NFAState()
        end_state.add_edge(Edge.empty(entry_state))

        nfa = self.expression.to_nfa()
        entry_state.add_edge(nfa.entry_edge)
        nfa.end_state.add_edge(Edge.empty(end_state))

        entry = Edge.empty(end_state)
        return NFA(entry, end_state)

