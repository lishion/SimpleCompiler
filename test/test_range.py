from unittest import TestCase
from lexer.range import RangeSearch
from lexer.state import CharRange


class TestRangeSearch(TestCase):

    def test_search(self):
        r = RangeSearch(
            [
                CharRange(1, 1),
                CharRange(2, 2),
                CharRange(3, 4),
                CharRange(5, 6),
            ]
        )
        print(r.search_range(CharRange(1, 4)))
        print(r.search_range(CharRange(1, 1)))
        print(r.search_range(CharRange(1, 2)))
        print(r.search_range(CharRange(1, 7)))

        print(r.contains(CharRange(1, 1)))
        print(r.contains(CharRange(5, 5)))
