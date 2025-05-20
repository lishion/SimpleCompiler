from collections import defaultdict
from ir import ConcreteBytecode, ConcreteInstr


def build_vtable(cb: ConcreteBytecode):
    cb.name = ['defaultdict', 'dict']
    cb.extend([
        ConcreteInstr("LOAD_GLOBAL", 0),  # defaultdict
        ConcreteInstr("LOAD_GLOBAL", 1),  # int
        ConcreteInstr("CALL", 1),  # defaultdict(int)
    ])
