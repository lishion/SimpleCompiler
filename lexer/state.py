from typing import List, Tuple, Optional, AnyStr
from typing import Union
from lexer.range import CharRange


class Edge:
    def __init__(self, char: Optional[Union[AnyStr, CharRange]], state: Union['NFAState', 'DFAState']):
        self.char = CharRange.code(char) if type(char) is str else char
        self.state = state

    @staticmethod
    def empty(state=None):
        return Edge(None, state)

    def is_empty(self): return self.char is None

    def __str__(self):
        return "---" + ("ε" if self.is_empty() else f"[{chr(self.char.start)}, {chr(self.char.end)}]") + "->"

    def __repr__(self):
        return self.__str__()


class NFAState:
    def __init__(self, edges: List[Edge] = None):
        self.edges: List[Edge] = edges or []
        self.accept_as = None

    def add_edge(self, edge: Edge):
        self.edges.append(edge)

    def __str__(self):
        return "[state]->\n" + "\n".join([str(edge) for edge in self.edges])

    def __repr__(self):
        return self.__str__()


class DFAState:
    def __init__(self, nfa_states: Tuple['NFAState'] = None, edges: List['Edge'] = None, accept_as=None):
        self.nfa_states = nfa_states or tuple()
        self.edges = edges or []
        self.edges_mapping = {e.input: e.state for e in self.edges}
        self.accept_as = accept_as

    def add_edge(self, edge: Edge):
        self.edges.append(edge)
        self.edges_mapping[edge.char] = edge.state

    def move_by(self, char):
        return self.edges_mapping.get(char)


class NFA:
    def __init__(self, entry_edge: Edge, end_state: NFAState):
        self.entry_edge = entry_edge
        self.end_state = end_state
