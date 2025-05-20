from unittest import TestCase

from bytecode import ConcreteBytecode, ConcreteInstr

from code_gen.indent import PythonCodeGenerator
from parser.expr import parse_proc
from lexer.lexer import BaseLexer
from grammer import TOKENS
from parser.scope import ScopeManager
from parser.types import FunctionSignature
from parser.visitor import SymbolVisitor, ReferenceResolveVisitor, EvalVisitor, PositionVisitor, SymbolDefinitionVisitor
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
        # import dis
        # dis.dis(a)



        bytecode = ConcreteBytecode()
        bytecode.consts = [{"a": 1}]
        bytecode.names = ["get"]
        bytecode.varnames = ["a"]
        bytecode.extend([
            ConcreteInstr("LOAD_CONST", 0),
            ConcreteInstr("LOAD_ATTR", (0<<1)|1),  # 加载 a
            ConcreteInstr("LOAD_CONST", 0),
            ConcreteInstr("CALL", 1),
        ])
        bytecode.varnames = ['a', 'b']
        bytecode.argcount = 2
        code = bytecode.to_code()
        # add_func = FunctionType(code, globals(), 'add')
        # print(ConcreteInstr("LOAD_FAST", 0).size)

        # class A:
        #     def __init__(self):
        #         self.b = 1
        #
        # dis.dis(A)


