from unittest import TestCase
from lexer.utils import generate_range, dis_join, split_range_by
from lexer.state import CharRange
from runtime.data import TypeName

class Test(TestCase):

    def test_type_name(self):
        x = TypeName("Vector", parameters=(TypeName("Vector", parameters=(TypeName("Int"),TypeName("Int1"))),))
        print(x)

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

    def test_(self):

        from bytecode import ConcreteInstr, ConcreteBytecode
        bytecode = ConcreteBytecode()
        bytecode.names = ['print']
        bytecode.consts = ['Hello World!', None]
        bytecode.varnames = ['a']
        bytecode.extend([ConcreteInstr("LOAD_CONST", 0),
                         ConcreteInstr("STORE_FAST", 0),
                         ConcreteInstr("LOAD_GLOBAL", 1),
                         ConcreteInstr("LOAD_FAST", 0),
                         ConcreteInstr("CALL", 1),
                         ConcreteInstr("POP_TOP"),
                         ConcreteInstr("LOAD_CONST", 1),
                         ConcreteInstr("RETURN_VALUE")])
        code = bytecode.to_code()
        exec(code)