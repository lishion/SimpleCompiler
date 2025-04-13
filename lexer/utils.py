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


# 将区间列表划分为不相交的子区间
def dis_join(ranges: List[CharRange]) -> List[CharRange]:
    sorted_point = set(reduce(lambda x, y: x + [y.start, y.end], ranges, []))
    return [CharRange(s, e) for s, e in generate_range(sorted_point)]


# 求 epsilon closure
def closure(state: NFAState) -> Tuple['NFAState']:
    res = {state}
    pending_states = [state]
    while pending_states:
        next_state = pending_states.pop(0)
        for edge in next_state.edges:
            if edge.is_empty():
                if edge.state not in res:
                    res.add(edge.state)
                    pending_states.append(edge.state)
    return tuple(res)


# nfa 状态机转换为 dfa 状态机，输出 dfa 状态机的初始状态
def nfa_to_dfa(nfa: NFA) -> DFAState:
    dfa_init_state = DFAState(nfa_states=closure(nfa.entry_edge.state))
    pending_states = [dfa_init_state]
    states_mapping = {}
    while pending_states:
        dfa_state = pending_states.pop(0)
        # 获取从当前 dfa state 能够进行转移的所有区间
        all_edges = reduce(
            lambda x, y: x + y,
            map(lambda x: x.edges, dfa_state.nfa_states),
            []
        )
        # 分割为不相交的子区间
        splits = dis_join([edge.char for edge in all_edges if edge.char])
        range_search = RangeSearch(splits)

        for state in dfa_state.nfa_states:
            new_edges = []
            for edge in state.edges:
                char = edge.char
                if not char:
                    new_edges.append(edge)
                    continue
                # 拆分为不相交的子区间作为新转移区间
                new_edges += [Edge(r, edge.state) for r in range_search.search_range(char)]
            state.edges = new_edges

        res = defaultdict(set)
        # 计算从 char 出发能够到达的所有 nfa state
        for state in dfa_state.nfa_states:
            for edge in state.edges:
                if edge.state:
                    res[edge.char].update(closure(edge.state))

        for chr_range, all_states in res.items():
            if chr_range is None:
                continue
            all_states = tuple(all_states)
            # 如果 nfa state 组成的 dfa state 已经存在，直接创建新转移
            if all_states in states_mapping:
                existed_dfa_state = states_mapping.get(all_states)
                dfa_state.add_edge(Edge(chr_range, existed_dfa_state))
            # 否则需要新建 dfa state
            else:
                accepts = [(s.accept_as.index, s.accept_as) for s in all_states if s.accept_as]
                new_dfa_state = DFAState(nfa_states=all_states)
                new_dfa_state.accept_as = min(accepts)[1] if accepts else None
                states_mapping[all_states] = new_dfa_state
                dfa_state.add_edge(Edge(chr_range, new_dfa_state))
                pending_states.append(new_dfa_state)
    return dfa_init_state


def split_range_by(start, end, split_chars):
    if not split_chars:
        return [(start, end)]
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
