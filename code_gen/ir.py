from dataclasses import dataclass
from enum import Enum
from typing import Any, List, Optional

from bytecode import ConcreteInstr, ConcreteBytecode
from bytecode.instr import UNSET


class ByteCodes(Enum):
    LOAD_CONST = "LOAD_CONST"
    LOAD_FAST = "LOAD_FAST"
    CALL = "CALL"
    RETURN_VALUE = "RETURN_VALUE"
    BINARY_OP = "BINARY_OP"
    LOAD_GLOBAL = "LOAD_GLOBAL"
    STORE_FAST = "STORE_FAST"
    STORE_GLOBAL = "STORE_GLOBAL"
    PUSH_NULL = "PUSH_NULL"
    MAKE_FUNCTION = "MAKE_FUNCTION"
    BINARY_SUBSCR = "BINARY_SUBSCR"
    STORE_SUBSCR = "STORE_SUBSCR"
    BUILD_CONST_KEY_MAP= "BUILD_CONST_KEY_MAP"
    LOAD_ATTR = "LOAD_ATTR"
    POP_JUMP_IF_FALSE = "POP_JUMP_IF_FALSE"
    COMPARE_OP = "COMPARE_OP"
    JUMP_FORWARD = "JUMP_FORWARD"
    JUMP_BACKWARD = "JUMP_BACKWARD"
    POP_TOP = "POP_TOP"
    RETURN_CONST = "RETURN_CONST"

JUMP_CMDS = {
    ByteCodes.JUMP_FORWARD,
    ByteCodes.JUMP_BACKWARD,
    ByteCodes.POP_JUMP_IF_FALSE
}


@dataclass(frozen=True)
class Label:
    global_index: int
    local_index: str

@dataclass
class CodeRepr:
    op_name: ByteCodes
    const: Any = None
    name: str = None
    var: str = None
    op_num: int = None
    flag: bool = None
    need_shift: bool = None
    label: Label = None
    current_offset: int = None
    null_const: bool = False

    def __str__(self):
        string = ''
        if self.const is not None:
            string = self.const
        elif self.name is not None:
            string = self.name
        elif self.var is not None:
            string = self.var
        elif self.op_num is not None:
            string = self.op_num
        elif self.label is not None:
            string = str(self.label)
        return f"{self.op_name.value.ljust(20, ' ')} {string}"

    def __repr__(self):
        return self.__str__()




@dataclass
class Comment:
    line: str

    def __str__(self):
        return f"====={self.line}====="


@dataclass
class ConcreteBytecodeConverter:
    # bytecode_obj: ConcreteBytecode
    # varnames_index: dict[str, int] = field(default_factory=dict)
    # names_index: dict[str, int] = field(default_factory=dict)
    # const_index: dict[str, int] = field(default_factory=dict)

    def __init__(self, bytecodes: List[CodeRepr|Comment]):
        self.bytecodes: List[CodeRepr|Comment] = bytecodes
        self.varnames_index = {}
        self.names_index = {}
        self.const_index = {}
        self.code_offset = 0
        self.code_offset_mapping = {}

    def _add(self, d: dict[str, Any], name):
        if name not in d:
            d[name] = len(d)
        return d[name]

    def add_var(self, name):
        return self._add(self.varnames_index, name)

    def add_const(self, val):
        return self._add(self.const_index, val)

    def add_name(self, name):
        return self._add(self.names_index, name)

    def _convert(self, code_repr: CodeRepr|Label) -> Optional[ConcreteInstr|CodeRepr]:
        if isinstance(code_repr, Label):
            self.code_offset_mapping[code_repr] = self.code_offset
            return None
        op_name = code_repr.op_name
        if op_name in JUMP_CMDS:
            code_repr.current_offset = self.code_offset
            self.code_offset += 2
            return code_repr # do not process jup cmd here, will handle in next round
        if code_repr.null_const:
            op_num = self.add_const(None)
        elif code_repr.const is not None:
            op_num = self.add_const(code_repr.const)
        elif code_repr.name:
            op_num = self.add_name(code_repr.name)
        elif code_repr.var:
            op_num = self.add_var(code_repr.var)
        elif code_repr.op_num is not None:
            op_num = code_repr.op_num
        else:
            op_num = UNSET
        if code_repr.need_shift:
            op_num = op_num << 1
        if code_repr.flag:
            op_num = op_num | 1
        res = ConcreteInstr(op_name.value, op_num)
        self.code_offset += res.size
        return res

    def show(self):
        for x in self.bytecodes:
            print(x)
        return self

    def convert(self) -> ConcreteBytecode:
        instructions = [self._convert(c) for c in self.bytecodes if not isinstance(c, Comment)]
        replace_offset_instr = []
        for instr in instructions:
            if not instr:
                continue
            if isinstance(instr, CodeRepr):
                label = instr.label
                op_name = instr.op_name.value
                if self.code_offset_mapping[label] > instr.current_offset:
                    offset = (self.code_offset_mapping[label] - (instr.current_offset + 2)) // 2
                else:
                    offset = ((instr.current_offset + 2) - self.code_offset_mapping[label]) // 2
                replace_offset_instr.append(ConcreteInstr(op_name, offset))
            else:
                replace_offset_instr.append(instr)

        bytecode = ConcreteBytecode(instructions=replace_offset_instr)
        bytecode.names = list(self.names_index.keys())
        bytecode.consts = list(self.const_index.keys())
        bytecode.varnames = list(self.varnames_index.keys())
        return bytecode

def repr_to_bytecode(bytecodes: List[CodeRepr|Comment]):
    return ConcreteBytecodeConverter(bytecodes).show().convert()