from unittest import TestCase
from parser.symbol import FunctionOverload

class TestFunctionOverload(TestCase):

    def test_function_overload(self):
        function1 = FunctionOverload(("a", "b"), "b", None, None)
        function2 = FunctionOverload(("a", "b"), "b", None, None)
        self.assertTrue(function1 == function2)
        self.assertTrue(function1 in {function2})

    def test_function_overload(self):
        function1 = FunctionOverload(("a", "b"), "b", None, None)
        function2 = FunctionOverload(("a", "b"), "b", None, None)
        self.assertTrue(function1 == function2)
        self.assertTrue(function1 in {function2})
