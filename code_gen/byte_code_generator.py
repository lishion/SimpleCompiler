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
        return [CodeRepr(ByteCodes.LOAD_FAST, var=node.identifier.name)]


    def visit_assign(self, node: 'AssignNode'):
        res = []
        res += node.assign_expr.accept(self)
        res.append(CodeRepr(ByteCodes.STORE_FAST, var=node.var.identifier.name))
        return res

    def visit_proc(self, node: 'ProcNode'):
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

        res = [
            Comment("main function start"),
            Comment("add echo to global"),
            CodeRepr(ByteCodes.LOAD_CONST, const=print_obj.to_code()),
            CodeRepr(ByteCodes.STORE_GLOBAL, name='echo'),

            Comment("init vtable & store to global"),
            CodeRepr(ByteCodes.PUSH_NULL),
            CodeRepr(ByteCodes.LOAD_GLOBAL, name='defaultdict', need_shift=True),
            CodeRepr(ByteCodes.LOAD_GLOBAL, name='dict', need_shift=True),
            CodeRepr(ByteCodes.CALL, op_num=1),
            CodeRepr(ByteCodes.STORE_GLOBAL, name='vtables'),
        ]
        for statement in node.children:
            if r := statement.accept(self):
                res += r
        return ConcreteBytecodeConverter(res).show().convert()

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
            res.append(Comment("add self as the first argument for object function"))
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

        func_def_bytecodes = [
            Comment(f"func def of '{node.name.name}' start")
        ]
        func_def_bytecodes += node.body.accept(self)
        func_def_bytecodes.append(Comment(f"func def of '{node.name.name}' end\n\n"))

        func_bc = repr_to_bytecode(func_def_bytecodes)
        func_bc.argcount = len(node.args) + 1 if node.trait_node else len(node.args)
        func_bc.name = node.name.name
        func_obj = func_bc.to_code()

        res = []
        target_type_name = node.trait_node and node.trait_node.target_type.name
        if target_type_name:
            res.append(Comment("load func object"))
            res.append(CodeRepr(ByteCodes.LOAD_CONST, const=func_obj))

            res.append(Comment("load vtable from global"))
            res.append(CodeRepr(ByteCodes.LOAD_GLOBAL, name='vtables', need_shift=True))
            res.append(CodeRepr(ByteCodes.LOAD_CONST, const=target_type_name))
            res.append(CodeRepr(ByteCodes.BINARY_SUBSCR))

            res.append(Comment("sotre function to global vtable"))
            res.append(CodeRepr(ByteCodes.LOAD_CONST, const=node.name.name))
            res.append(CodeRepr(ByteCodes.STORE_SUBSCR))

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

        res: List[CodeRepr|Comment] = [
            Comment("start to create a object")
        ]
        for assign in node.body:
            res += assign.assign_expr.accept(self)

        res.append(Comment("add method to vtables"))
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
        data_bytes = node.data.accept(self)
        """
            implement dynamic bind in runtime
            every obj has a special attribute $_vatable__, which stores trait functions.
            let student = Student{name="lily"}
            impl Write for Student{
                def toString() -> String{
                    return self.name;
                }
            }
            student would be a python dict:
            {
                "name":  "lily",
                "$vtable": {
                    "toString": [function type in python]
                }   
            } 
            for a attribute operation, we don't know it's trait function or a normal attribute.
            so we need to use: 
            d.get("$vtable", {}).get("attr", d.get("attr")) to get the final result.
                                             ^^^^^^^^^^^^^ use normal attribute as default value
        """
        res: List[CodeRepr|Comment] = [
            Comment("get vtable from dict")
        ]
        res += data_bytes
        res.append(CodeRepr(ByteCodes.LOAD_ATTR, name='get', need_shift=True, flag=True))
        res.append(CodeRepr(ByteCodes.LOAD_CONST, const='$__vtable__'))
        res.append(CodeRepr(ByteCodes.CALL, op_num=1))

        res.append(Comment("get method object from vtable"))
        res.append(CodeRepr(ByteCodes.LOAD_ATTR, name='get', need_shift=True, flag=True))
        res.append(CodeRepr(ByteCodes.LOAD_CONST, const=node.attr.name))

        res.append(Comment("set the default value to attr start"))
        res += data_bytes
        res.append(CodeRepr(ByteCodes.LOAD_ATTR, name='get', need_shift=True, flag=True))
        res.append(CodeRepr(ByteCodes.LOAD_CONST, const=node.attr.name))
        res.append(CodeRepr(ByteCodes.CALL, op_num=1))
        res.append(Comment("set the default value to attr end"))
        res.append(CodeRepr(ByteCodes.CALL, op_num=2))
        res.append(Comment("get attribute completed"))

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
        return res

    def visit_trait_impl(self, node: 'TraitImplNode'):
        res = []
        for node in node.impls:
            res += node.accept(self)
        return res



