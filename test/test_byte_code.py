from unittest import TestCase

from bytecode import ConcreteBytecode, ConcreteInstr

from code_gen.script import PythonCodeGenerator
from parser.expr import parse_proc
from lexer.lexer import BaseLexer
from grammer import TOKENS
from parser.scope import ScopeManager
from parser.types import FunctionSignature
from parser.visitor1 import SymbolVisitor, ReferenceResolveVisitor, EvalVisitor, PositionVisitor, SymbolDefinitionVisitor
from parser.utils import init_global_scope
from error.reporter import SourceCodeMaker, ErrorReporter
from runtime.data import MetaManager
from runtime import *
from dis import dis

class Student:
    def __init__(self, name):
        self.name = name
        self.student = None

class Test(TestCase):


    def test_string(self):
        # from bytecode import ConcreteBytecode, ConcreteInstr
        # from types import FunctionType
        #
        # # 创建字节码对象
        # print_obj = ConcreteBytecode()
        # print_obj.name = 'echo'
        # print_obj.names = ['print']  # 全局名称表
        # print_obj.varnames = ['string']
        # print_obj.argcount = 1
        #
        # # 正确的指令序列 (Python 3.11+)
        # print_obj.extend([
        #     ConcreteInstr("PUSH_NULL"),
        #     ConcreteInstr("LOAD_GLOBAL", 0),  # 压入 print 函数
        #     ConcreteInstr("LOAD_FAST", 0),  # 压入参数 string
        #     ConcreteInstr("CALL", 1),  # 调用函数 (1个参数)
        #     ConcreteInstr("RETURN_VALUE")  # 返回结果
        # ])
        #
        # # 转换为函数并测试
        # func = FunctionType(print_obj.to_code(), {'print': print})
        # func("Hello World")  # 正常输出: Hello World

        # def a():
        #     def a1(): pass
        #
        #     def b():
        #         a1()
        import dis
        # dis.dis(a)

        from bytecode import ConcreteBytecode, ConcreteInstr
        import types

        def test():
            if 2 >= 1:
                b =  1 + 2
                echo(b)

        dis.dis(test)
        for x in dis.get_instructions(test):
            print(x)

        # bytecode = test.__code__.co_code
        # for i, instr in enumerate(dis.Bytecode(bytecode)):
        #     print(f"{i}: {instr.opname} (arg={instr.arg})")

        # 设置常量和变量
        consts = [None, 1, -1]
        varnames = ['x']

        # 初始化 bytecode 对象
        code = ConcreteBytecode()
        code.argcount = 1
        code.name = "foo"
        code.filename = "example"
        code.flags = 0
        code.consts = consts
        code.varnames = varnames

        # 指令序列（字节码偏移基于具体跳转计算）
        instructions = [
            # if x > 0:
            ConcreteInstr('LOAD_FAST', 0),  # x
            ConcreteInstr('LOAD_CONST', 1),  # 1
            ConcreteInstr('COMPARE_OP', 4),  # >
            ConcreteInstr('POP_JUMP_IF_FALSE', 2),  # 跳到 else 分支（指令索引）

            # if body: return 1
            ConcreteInstr('LOAD_CONST', 1),  # 1
            ConcreteInstr('RETURN_VALUE'),

            # else body: return -1
            ConcreteInstr('LOAD_CONST', 2),  # -1
            ConcreteInstr('RETURN_VALUE'),
        ]

        code.extend(instructions)

        # 转换为 code 对象
        pycode = code.to_code()

        # 构造函数
        foo = types.FunctionType(pycode, globals())

        # 测试
        print(foo(10))  # 输出 1
        print(foo(-5))  # 输出 -1
        print(dis.cmp_op)

        instr = ConcreteInstr("BINARY_OP", 0)
        print(instr.size)
        print(instr.assemble())  # 展示实际生成的字节码

