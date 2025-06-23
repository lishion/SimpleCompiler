from typing import List, Tuple, Any

from bytecode import ConcreteBytecode, ConcreteInstr


from parser.node import LiteralNode, VarNode, AssignNode, BinaryOpNode, ProcNode, FunctionDefNode, FunctionCallNode, \
    BlockNode, ReturnNode, VarDefNode, StructInitNode, AttributeNode, TraitImplNode, IfStatement, LoopStatement, \
    ContinueOrBreak
from parser.types import VarType
from parser.visitor.visitor import Visitor
from dataclasses import dataclass, field
from bytecode.instr import Compare
from code_gen.ir import CodeRepr, ByteCodes, ConcreteBytecodeConverter, Comment, repr_to_bytecode, Label
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
    '^': 12
}

COMPARE_OP_MAP = {
    "<": 0 << 4,
    "<=": 1 << 4,
    "==": 2 << 4,
    "!=": 3 << 4,
    ">": 4 << 4,
    ">=": 5 << 4,
    "in": 6,
    "not in": 7,
    "is": 8,
    "is not": 9,
    "exception match": 10,
    "BAD": 11
}


class BytecodeGenerateVisitor(Visitor):


    def __init__(self):
        self._current_if_statement_index = -1
        self._current_loop_statement_index = -1

    def visit_lit(self, node: 'LiteralNode'):
        match VarType(node.literal_type):
            case VarType.Float: val = float(node.val)
            case VarType.Int: val = int(node.val)
            case VarType.Bool if node.val == "true": val = True
            case VarType.Bool if node.val == "false": val = False
            case VarType.String: val = node.val[1: -1]
            case _: raise Exception(f"unknown literal type {node.val}")
        return [CodeRepr(ByteCodes.LOAD_CONST, const=val)]

    def visit_bin_op(self, node: 'BinaryOpNode'):
        res = []
        res += node.left.accept(self)
        res += node.right.accept(self)
        if node.op in BINARY_OP_MAP:
            res.append(CodeRepr(ByteCodes.BINARY_OP, op_num=BINARY_OP_MAP[node.op]))
        elif node.op in COMPARE_OP_MAP:
            res.append(CodeRepr(ByteCodes.COMPARE_OP, op_num=COMPARE_OP_MAP[node.op]))
        else:
            raise ValueError("unknown op %s" % node.op)
        return res


    def visit_var(self, node: 'VarNode'):
        if node.identifier.string == "echo":
            return [CodeRepr(ByteCodes.LOAD_GLOBAL, name="echo")]
        return [CodeRepr(ByteCodes.LOAD_FAST, var=node.identifier.string)]


    def visit_assign(self, node: 'AssignNode'):
        res = []
        res += node.assign_expr.accept(self)
        res.append(CodeRepr(ByteCodes.STORE_FAST, var=node.var.identifier.string))
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
        res.append(CodeRepr(ByteCodes.RETURN_CONST, null_const=True))
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
        res.append(CodeRepr(ByteCodes.POP_TOP))
        res.append(Comment(f"==function call end"))
        return res

    def visit_loop(self, node: 'LoopStatement'):
        pass

    def visit_function_def(self, node: 'FunctionDefNode'):

        func_def_bytecodes = [
            Comment(f"func def of '{node.name.string}' start")
        ]
        func_def_bytecodes += node.body.accept(self)
        func_def_bytecodes.append(Comment(f"func def of '{node.name.string}' end\n\n"))

        func_bc = repr_to_bytecode(func_def_bytecodes)
        func_bc.argcount = len(node.args) + 1 if node.trait_node else len(node.args)
        func_bc.string = node.name.string
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

            res.append(Comment("store function to global vtable"))
            res.append(CodeRepr(ByteCodes.LOAD_CONST, const=node.name.string))
            res.append(CodeRepr(ByteCodes.STORE_SUBSCR))

        else:
            res.append(CodeRepr(ByteCodes.LOAD_CONST, const=func_obj))
            res.append(CodeRepr(ByteCodes.STORE_FAST, var=node.name.string))

        return res

    def visit_var_def(self, node: 'VarDefNode'):
        res = []
        if node.init_expr:
            res += node.init_expr.accept(self)
            res.append(CodeRepr(ByteCodes.STORE_FAST, var = node.var_node.string))
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

    def visit_struct_init(self, node: 'StructInitNode'):
        key_names = tuple([expr.var.identifier.string for expr in node.body] + ['$__vtable__'])

        res: List[CodeRepr|Comment] = [
            Comment("start to create an object")
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
        res.append(CodeRepr(ByteCodes.LOAD_CONST, const=node.attr.string))

        res.append(Comment("set the default value to attr start"))
        res += data_bytes
        res.append(CodeRepr(ByteCodes.LOAD_ATTR, name='get', need_shift=True, flag=True))
        res.append(CodeRepr(ByteCodes.LOAD_CONST, const=node.attr.string))
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
        for node in node.functions:
            res += node.accept(self)
        return res

    def visit_if(self, node: 'IfStatement'):
        res: List[CodeRepr|Comment|Label] = [
            Comment("if statement start")
        ]
        self._current_if_statement_index += 1
        if_index = self._current_if_statement_index
        single_if = len(node.branches) and not node.else_branch
        for index, v in enumerate(node.branches):
            condition, body = v
            res.append(Label(if_index, str(index)))
            res += condition.accept(self)
            res.append(CodeRepr(ByteCodes.POP_JUMP_IF_FALSE, label = Label(if_index, str(index + 1))))
            res += body.accept(self)
            # jump to end if there is another branch/else
            single_if or res.append(CodeRepr(ByteCodes.JUMP_FORWARD, label = Label(if_index, 'end')))
        res.append(Label(if_index, str(index + 1)))
        if node.else_branch:
            res += node.else_branch.accept(self)
        res.append(Label(if_index, 'end'))
        # res.append(CodeRepr(ByteCodes.RETURN_CONST, null_const=True))
        res.append(Comment("if statement end"))
        return res

    def visit_loop(self, node: 'LoopStatement'):
        self._current_if_statement_index += 1
        loop_index = self._current_if_statement_index
        res: List[Label|CodeRepr] = [Comment("while statement start"), Label(loop_index, 'loop_start')]
        res += node.condition.accept(self)
        res.append(CodeRepr(ByteCodes.POP_JUMP_IF_FALSE, label=Label(loop_index, 'loop_end')))
        undecided_cmd: List[CodeRepr] = node.body.accept(self)
        for cmd in undecided_cmd:
            match cmd:
                case CodeRepr(op_name=op_name, label=label) if label and label.global_index == -1:
                    new_cmd = CodeRepr(op_name, label=Label(loop_index, label.local_index))
                case _:
                    new_cmd = cmd
            res.append(new_cmd)
        res.append(CodeRepr(ByteCodes.JUMP_BACKWARD, label=Label(loop_index, 'loop_start')))
        res.append(Label(loop_index, 'loop_end'))
        res.append(CodeRepr(ByteCodes.RETURN_CONST, null_const=True))
        return res

    def visit_continue_or_break(self, node: 'ContinueOrBreak'):
        if node.kind == "continue":
            return [CodeRepr(ByteCodes.JUMP_BACKWARD, label=Label(-1, 'loop_start'))]
        return [CodeRepr(ByteCodes.JUMP_FORWARD, label=Label(-1, 'loop_end'))]