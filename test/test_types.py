from tokenize import String
from unittest import TestCase

from parser.types import FunctionSignature, Type, is_primitive


class TestFunctionSignature(TestCase):

    def test_to_string(self):
        a = FunctionSignature(
            (
                FunctionSignature((Type("Int"), Type("Int")), Type("Bool")),
            ),
            Type("Int"),
        )
        print(a)

    def test_eq(self):
        a = FunctionSignature(
            (
                FunctionSignature((Type("Int"), Type("Int")), Type("Bool")),
            ),
            Type("Int"),
        )

        b = FunctionSignature(
            (
                FunctionSignature((Type("Int"), Type("Int")), Type("Bool")),
            ),
            Type("Int"),
        )

        print(a == b)


class Test(TestCase):
    def test_is_primitive(self):
        self.assertTrue(is_primitive("Bool"))
        self.assertFalse(is_primitive("Bool1"))
