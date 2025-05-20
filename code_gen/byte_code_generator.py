from typing import List, Tuple, Any

from bytecode import ConcreteBytecode, ConcreteInstr

from parser.node import LiteralNode, VarNode, AssignNode, BinaryOpNode, ProcNode, FuncDefNode, FunctionCallNode, \
    BlockNode, ReturnNode, VarDefNode, DataInitNode, AttributeNode, TraitImplNode
from parser.types import VarType
from parser.visitor import Visitor
from dataclasses import dataclass, field
from code_gen.ir import CodeRepr, ByteCodes, ConcreteBytecodeConverter, Comment, repr_to_bytecode
from bytecode.instr import BinaryOp


@dataclass
class StackFrame:
    bytecode_obj: ConcreteBytecode
    varnames_index: dict[str, int] = field(default_factory=dict)
    names_index: dict[str, int] = field(default_factory=dict)
    const_index: dict[str, int] = field(default_factory=dict)

    def add_var(self, name):
        self.bytecode_obj.varnames.append(name)
        self.varnames_index[name] = len(self.bytecode_obj.varnames) - 1
        return self.varnames_index[name]

    def add_const(self, val):
        if val in self.bytecode_obj.consts:
            return self.const_index[val]
        self.bytecode_obj.consts.append(val)
        self.const_index[val] = len(self.bytecode_obj.consts) - 1
        return self.const_index[val]

    def add_global(self, name):
        self.bytecode_obj.names.append(name)
        self.names_index[name] = len(self.bytecode_obj.names) - 1
        return self.names_index[name]

    def append_code(self, op_name: str, op_num:int = None):
        self.bytecode_obj.append(ConcreteInstr(op_name, arg=UNSET if op_num is None else op_num))

    def append_codes(self, *codes: str|Tuple[str, int]):
        for c in codes:
            if isinstance(c, str):
                self.append_code(c)
            else:
                opcode, opnum = c
                self.append_code(opcode, opnum)




BINARY_OP_MAP = {
    '+': 0,
    'and': 1,
    '//': 2,
    '<<': 3,
    'MATRIX_MULTIPLY': 4,
    '*': 5,
    '%': 6,  # `%`
    'or': 7,
    '**': 8,
    '>>': 9,
    '-': 10,
    '/': 11,
    '^': 12,
}


class BytecodeGenerateVisitor(Visitor):

    def __init__(self):
        self.stack_frames: List[StackFrame] = []
        self.current_frame_index: int = -1
        self.is_func_call = False


    def push(self) -> StackFrame:
        self.stack_frames.append(StackFrame(ConcreteBytecode()))
        return self.stack_frames[-1]

    def pop(self) -> StackFrame:
        return self.stack_frames.pop(-1)

    def append_code(self, op_name: str, op_num:int = None):
        self.current_frame.append_bytecode(ConcreteInstr(op_name, arg=UNSET if op_num is None else op_num))

    def append_codes(self, *codes: str|Tuple[str, int]):
        for c in codes:
            if isinstance(c, str):
                self.append_code(c)
            else:
                opcode, opnum = c
                self.append_code(opcode, opnum)

    @property
    def current_frame(self) -> StackFrame:
        return self.stack_frames[-1]

    def visit_lit(self, node: 'LiteralNode'):
        match VarType(node.literal_type):
            case VarType.Float: val = float(node.val)
            case VarType.Int: val = int(node.val)
            case VarType.Bool: val = bool(node.val)
            case VarType.String: val = node.val[1: -1]
            case _: val = node.val
        return [CodeRepr(ByteCodes.LOAD_CONST, const=val)]

    def visit_bin_op(self, node: 'BinaryOpNode'):
        res = []
        res += node.left.accept(self)
        res += node.right.accept(self)
        res.append(CodeRepr(ByteCodes.BINARY_OP, BINARY_OP_MAP[node.op]))


    def visit_var(self, node: 'VarNode'):
        if node.identifier.name == "echo":
            return [CodeRepr(ByteCodes.LOAD_GLOBAL, name="echo")]
        # if node.identifier.name not in self.current_frame.varnames_index:
        #     raise Exception(
        #         f"{node.identifier.name} not in current frame {list(self.current_frame.varnames_index.keys())}")
        return [CodeRepr(ByteCodes.LOAD_FAST, var=node.identifier.name)]


    def visit_assign(self, node: 'AssignNode'):
        res = []
        res += node.assign_expr.accept(self)
        res.append(CodeRepr(ByteCodes.STORE_FAST, var=node.var.identifier.name))
        return res

    def visit_proc(self, node: 'ProcNode'):

        # main = ConcreteBytecode()


        # self.push()
        # self.current_frame.add_global('echo')
        # self.current_frame.add_global('defaultdict')
        # self.current_frame.add_global('dict')

        # self.current_frame.bytecode_obj.name = "<module>"
        # self.current_frame.bytecode_obj.argcount = 0

        print_obj = ConcreteBytecode()
        print_obj.name = 'echo'
        print_obj.names = ['print']
        print_obj.varnames = ['string']
        print_obj.argcount = 1
        print_obj.extend([
            ConcreteInstr("PUSH_NULL"),
            ConcreteInstr("LOAD_GLOBAL", 0),
            ConcreteInstr("LOAD_FAST", 0),
            ConcreteInstr("CALL", 1),
            ConcreteInstr("RETURN_VALUE"),
        ])

        # codes = (
        #     ("LOAD_CONST", const_index),
        #     ("STORE_GLOBAL", self.current_frame.add_global('echo')),
        #
        #     # init vtable
        #     "PUSH_NULL",
        #     ("LOAD_GLOBAL", self.current_frame.names_index['defaultdict'] << 1),
        #     ("LOAD_GLOBAL", self.current_frame.names_index['dict'] << 1),
        #     ("CALL", 1),
        #     ("STORE_GLOBAL", self.current_frame.add_global('vtables'))
        # )
        res = [
            Comment("add echo to global"),
            CodeRepr(ByteCodes.LOAD_CONST, const=print_obj.to_code()),
            CodeRepr(ByteCodes.STORE_GLOBAL, name='echo'),

            CodeRepr(ByteCodes.PUSH_NULL),
            Comment("init vtable"),
            CodeRepr(ByteCodes.LOAD_GLOBAL, name='defaultdict', need_shift=True),
            CodeRepr(ByteCodes.LOAD_GLOBAL, name='dict', need_shift=True),
            CodeRepr(ByteCodes.CALL, op_num=1),
            CodeRepr(ByteCodes.STORE_GLOBAL, name='vtables'),
        ]
        for statement in node.children:
            if r := statement.accept(self):
                res += r
        return ConcreteBytecodeConverter(res).convert()

    def visit_block(self, node: 'BlockNode'):
        res = []
        for s in node.stmts:
            if r := s.accept(self):
                res += r
        return res

    def visit_function_call(self, node: 'FunctionCallNode'):
        res = [
            Comment(f"==function call start"),
            CodeRepr(ByteCodes.PUSH_NULL)
        ]
        res += node.call_source.accept(self)
        res.append(CodeRepr(ByteCodes.MAKE_FUNCTION, op_num=0))
        is_trait = False
        if isinstance(node.call_source, AttributeNode):
            res += node.call_source.data.accept(self)
            is_trait = True
        for i, arg in enumerate(node.args):
            res += arg.accept(self)
        res.append(CodeRepr(ByteCodes.CALL, op_num=(len(node.args) + 1 if is_trait else len(node.args))))
        res.append(Comment(f"==function call end"))
        return res

    def visit_if(self, node: 'IfStatement'):
        pass

    def visit_loop(self, node: 'LoopStatement'):
        pass

    def visit_func_def(self, node: 'FuncDefNode'):
        # outer = self.current_frame
        # bytecode_obj = ConcreteBytecode()
        # bytecode_obj.argcount = len(node.args) + 1 if node.trait_node else len(node.args)
        # bytecode_obj.name = node.name.name
        bytecodes = []
        # if node.trait_node:
        #     bytecodes.append(bytecodes.append(CodeRepr(ByteCodes.LOAD_FAST, var=arg.var_node.name)))
        # for arg in node.args:
        #     bytecodes.append(CodeRepr(ByteCodes.LOAD_FAST, var=arg.var_node.name))
        bytecodes += node.body.accept(self)
        current = repr_to_bytecode(bytecodes)
        current.argcount = len(node.args) + 1 if node.trait_node else len(node.args)
        current.name = node.name.name
        print(f"function def {node.name.name} start ==")
        print('varnames', current.varnames)
        print('consts',current.consts)
        for x in current:
            print(x)
        print("function def end ==\n")
        # const_index = outer.add_const()
        # var_index = outer.add_var(node.name.name)
        target_type_name = node.trait_node and node.trait_node.target_type.name
        func_obj = current.to_code()
        res = []
        if target_type_name:

            res.append(CodeRepr(ByteCodes.LOAD_CONST, const=func_obj))

            res.append(Comment("load vtable"))
            res.append(CodeRepr(ByteCodes.LOAD_GLOBAL, name='vtables', need_shift=True))
            res.append(CodeRepr(ByteCodes.LOAD_CONST, const=target_type_name))
            res.append(CodeRepr(ByteCodes.BINARY_SUBSCR))

            res.append(Comment("sotre vtable"))
            res.append(CodeRepr(ByteCodes.LOAD_CONST, const=node.name.name))
            res.append(CodeRepr(ByteCodes.STORE_SUBSCR))

            # get vtable container of this type
            # outer.append_bytecode(ConcreteInstr("LOAD_GLOBAL", outer.names_index['vtables'] << 1))
            # outer.append_bytecode(ConcreteInstr("LOAD_CONST", outer.add_const(target_type_name)))
            # outer.append_bytecode(ConcreteInstr("BINARY_SUBSCR"))

            # store function object to corresponding vtable
            # res.append(Comment("store vtable"))
            # res.append(CodeRepr(ByteCodes.LOAD_CONST, const=node.name.name))
            # res.append(CodeRepr(ByteCodes.BINARY_SUBSCR))
            #
            # res.append(CodeRepr(ByteCodes.STORE_SUBSCR))
            #outer.append_bytecode(ConcreteInstr("STORE_SUBSCR"))

            # outer.append_bytecode(ConcreteInstr("PUSH_NULL"))
            # outer.append_bytecode(ConcreteInstr("LOAD_GLOBAL", outer.add_global("print") << 1))
            # outer.append_bytecode(ConcreteInstr("LOAD_GLOBAL", outer.names_index['vtables'] << 1))
            # outer.append_bytecode(ConcreteInstr("CALL", 1))


        else:
            res.append(CodeRepr(ByteCodes.LOAD_CONST, const=func_obj))
            res.append(CodeRepr(ByteCodes.STORE_FAST, var=node.name.name))
        return res

    def visit_var_def(self, node: 'VarDefNode'):
        res = []
        if node.init_expr:
            res += node.init_expr.accept(self)
            res.append(CodeRepr(ByteCodes.STORE_FAST, var = node.var_node.name))
        return res

    def visit_type(self, node: 'TypeNode'):
        pass

    def visit_type_def(self, node: 'TypeNode'):
        pass

    def visit_return(self, node: 'ReturnNode'):
        res = []
        res += node.expr.accept(self)
        res.append(CodeRepr(ByteCodes.RETURN_VALUE))
        return res

    def visit_identifier(self, node: 'IdNode'):
        pass

    def visit_type_init(self, node: 'DataInitNode'):
        key_names = tuple([expr.var.identifier.name for expr in node.body] + ['$__vtable__'])
        # key_index = self.current_frame.add_const(key_names)

        res = []
        for assign in node.body:
            res += assign.assign_expr.accept(self)
        # GET Vtable of type
        # self.append_code("LOAD_GLOBAL", self.current_frame.names_index['vtables'] << 1)
        # self.append_code("LOAD_CONST", self.current_frame.add_const(node.type_name.name))
        # self.append_code("BINARY_SUBSCR")
        #
        # self.append_code("LOAD_CONST", key_index)
        # self.append_code("BUILD_CONST_KEY_MAP", len(node.body) + 1)

        res.append(CodeRepr(ByteCodes.LOAD_GLOBAL, name='vtables', need_shift=True))
        res.append(CodeRepr(ByteCodes.LOAD_CONST, const=node.type_name.name))
        res.append(CodeRepr(ByteCodes.BINARY_SUBSCR))

        res.append(CodeRepr(ByteCodes.LOAD_CONST, const=key_names))
        res.append(CodeRepr(ByteCodes.BUILD_CONST_KEY_MAP, op_num=len(node.body) + 1))

        return res





        # self.append_code("LOAD_CONST", self.current_frame.add_const("$vtable"))




    def visit_function_type(self, node: 'FunctionTypeNode'):
        pass

    def visit_attribute(self, node: 'AttributeNode'):
        is_func_call = self.is_func_call
        self.is_func_call = False
        data_bytes = node.data.accept(self)
        res = data_bytes[:]
        res.append(CodeRepr(ByteCodes.LOAD_ATTR, name='get', need_shift=True, flag=True))
        res.append(CodeRepr(ByteCodes.LOAD_CONST, const='$__vtable__'))
        res.append(CodeRepr(ByteCodes.CALL, op_num=1))
        res.append(CodeRepr(ByteCodes.LOAD_ATTR, name='get', need_shift=True, flag=True))
        res.append(CodeRepr(ByteCodes.LOAD_CONST, const=node.attr.name))

        res += data_bytes
        res.append(CodeRepr(ByteCodes.LOAD_ATTR, name='get', need_shift=True, flag=True))
        res.append(CodeRepr(ByteCodes.LOAD_CONST, const=node.attr.name))
        res.append(CodeRepr(ByteCodes.CALL, op_num=1))
        res.append(CodeRepr(ByteCodes.CALL, op_num=2))

        # self.append_codes(
        #     # try load attr from vtable
        #     ("LOAD_ATTR", (self.current_frame.add_global("get") << 1) | 1),
        #     ("LOAD_CONST", self.current_frame.add_const("$__vtable__")),
        #     ("CALL", 1),
        #
        #     ("LOAD_ATTR", (self.current_frame.add_global("get") << 1) | 1),
        #     ("LOAD_CONST", self.current_frame.add_const(node.attr.name)),
        #
        # )
        #
        #
        # node.data.accept(self)
        # self.append_codes(
        #     ("LOAD_ATTR", (self.current_frame.add_global("get") << 1) | 1),
        #     ("LOAD_CONST", self.current_frame.add_const(node.attr.name)),
        #     ("CALL", 1),
        #     # us `or` operator to get final attr
        #     ("CALL", 2)
        # )
        self.is_func_call = is_func_call
        return res

    def visit_trait_impl(self, node: 'TraitImplNode'):
        res = []
        for node in node.impls:
            res += node.accept(self)
        return res



