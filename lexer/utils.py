from typing import *
from lexer.state import CharRange, Edge, DFAState, NFAState, NFA
from functools import reduce
from collections import defaultdict
from lexer.range import RangeSearch


def generate_range(ranges: Iterable[int]):
    sorted_point = list(sorted(set(ranges)))
    res_ranges = [(x, x) for x in sorted_point]
    for i, point in enumerate(sorted_point[:-1]):
        next_point = sorted_point[i + 1]
        if next_point - point >= 2:
            res_ranges.append((point + 1, next_point - 1))
    return res_ranges


def dis_join(ranges: List[CharRange]) -> List[CharRange]:
    sorted_point = set(reduce(lambda x, y: x + [y.start, y.end], ranges, []))
    return [CharRange(s, e) for s, e in generate_range(sorted_point)]


def closure(state: NFAState) -> Tuple['NFAState']:
    res = {state}
    next = [state]
    while next:
        next_state = next.pop(0)
        for edge in next_state.edges:
            if edge.is_empty():
                if edge.state not in res:
                    res.add(edge.state)
                    next.append(edge.state)
    return tuple(res)


def nfa_to_dfa(nfa: NFA) -> DFAState:
    dfa_start_state = DFAState(nfa_states=closure(nfa.entry_edge.state))
    pending_states = [dfa_start_state]
    states_mapping = {}
    while pending_states:
        next_dfa_state = pending_states.pop(0)
        res = defaultdict(set)
        all_edges = reduce(
            lambda x, y: x + y,
            map(lambda x: x.edges, next_dfa_state.nfa_states),
            []
        )
        splits = dis_join([edge.char for edge in all_edges if edge.char])
        range_search = RangeSearch(splits)

        for state in next_dfa_state.nfa_states:
            new_edges = []
            for edge in state.edges:
                char = edge.char
                if not char:
                    new_edges.append(edge)
                    continue
                new_edges += [Edge(r, edge.state) for r in range_search.search_range(char)]
            state.edges = new_edges

        for state in next_dfa_state.nfa_states:
            for edge in state.edges:
                if edge.state:
                    res[edge.char].update(closure(edge.state))

        for chr_range, all_states in res.items():
            if chr_range is None:
                continue
            all_states = tuple(all_states)
            if all_states in states_mapping:
                dfa_state = states_mapping.get(all_states)
                next_dfa_state.add_edge(Edge(chr_range, dfa_state))
            else:
                accepts = [(s.accept_as.index, s.accept_as) for s in all_states if s.accept_as]
                dfa_state = DFAState(nfa_states=all_states)
                dfa_state.accept_as = min(accepts) if accepts else None
                states_mapping[all_states] = dfa_state
                next_dfa_state.add_edge(Edge(chr_range, dfa_state))
                pending_states.append(dfa_state)
    return dfa_start_state


def match(nfa, string):
    dfa = nfa_to_dfa(nfa)
    for c in string:
        if dfa.move_by(c) is not None:
            dfa = dfa.move_by(c)
        else:
            print(f"error, expect {list(dfa.edges_mapping.keys())} but got {c}")
            return
    if not dfa.accept_as:
        print("unexpect EOF")


def split_range_by(start, end, split_chars):
    chars = sorted(list(map(ord, split_chars)))
    if chars[0] != start:
        chars = [start] + chars
    if chars[-1] != end:
        chars.append(end)
    ranges = []
    for i, ch in enumerate(chars[1:], start=1):
        if ch - chars[i - 1] > 1:
            ranges.append((chars[i - 1] + 1, ch - 1))
    return ranges


if __name__ == '__main__':
    dis_join([
        CharRange(1, 3),
        CharRange(2, 4)
    ])
