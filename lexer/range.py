from typing import List, Optional
from bisect import bisect_left
from dataclasses import dataclass


@dataclass(frozen=True)
class CharRange:
    start: int
    end: int

    @staticmethod
    def code(char_code: int):
        return CharRange(char_code, char_code)

    @staticmethod
    def char(char: str):
        char_code = ord(char)
        return CharRange(char_code, char_code)

    @staticmethod
    def index(char: int):
        return CharRange(char, char)

    # 判断一个值是否在该范围内
    def cover(self, start: int, end: Optional[int]=None):
        if end is None:
            return self.start <= start <= self.end
        return self.start <= start and end <= self.end

    # 判断一个 range 是否在该范围内
    def cover_range(self, r: 'CharRange'):
        return self.cover(r.start, r.end)


class RangeSearch:
    def __init__(self, ranges: List[CharRange]):
        self._ranges = ranges
        self._sorted_ranges = list(sorted(self._ranges, key=lambda x: x.start))
        self._ranges_start = list(map(lambda x: x.start, self._sorted_ranges))
        self._ranges_set = set(ranges)

    def search_range(self, target: CharRange):
        if target.start == target.end:
            return [target] if target in self._ranges_set else []
        start_index = bisect_left(self._ranges_start, target.start)
        res = []
        for r in self._sorted_ranges[start_index:]:
            if target.cover_range(r):
                res.append(r)
            else:
                break
        return res

    def search_cover(self, target: CharRange):
        if target in self._ranges_set:
            return target
        start_index = bisect_left(self._ranges_start, target.start)
        if start_index == 0:
            return None
        for r in self._sorted_ranges[start_index - 1:]:
            if r.cover_range(target):
                return r
        return None

    def contains(self, target: CharRange):
        if target in self._ranges_set:
            return True
        start_index = bisect_left(self._ranges_start, target.start)
        for r in self._sorted_ranges[start_index:]:
            if r.cover_range(target):
                return True
        return False


