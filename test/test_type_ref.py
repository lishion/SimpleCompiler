from unittest import TestCase

from parser.symbol_type import TypeRef, TraitRef
from parser.visitor.utils import map_filter


class Test(TestCase):
    def test_type_ref(self):
        self.assertEqual(
            TypeRef('a', parameters=[TypeRef('b', constraints=[TraitRef('c')])]),
            TypeRef('a', parameters=[TypeRef('c', constraints=[TraitRef('c')])]),
        )

    def test_filter(self):
        x = map_filter([1, 2, 3], mapper=lambda x: x +1)