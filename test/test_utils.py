from unittest import TestCase
from lexer.utils import generate_range, dis_join, split_range_by
from lexer.state import CharRange


class Test(TestCase):

    def test_split(self):
        res = generate_range([1, 2, 5, 10, 25])
        print(res)

        res = generate_range([1, 2, 3])
        print(res)

        res = generate_range([1, 2, 3, 4])
        print(res)

        res = generate_range([1, 2])
        print(res)

        res = generate_range([1, 2, 3, 65535])
        print(res)

    def test_dis_join(self):
        res = dis_join([
            CharRange(1, 3),
            CharRange(2, 65535)
        ])
        print(res)

    def test_split_range(self):
        print(split_range_by(0, 65535, '"='))