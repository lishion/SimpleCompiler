from typing import Optional, Dict, List, Tuple, Callable, Any, Set
from enum import Enum
from dataclasses import dataclass
from parser.types import Type, FunctionSignature, FunctionOverloadType, StructureType, TraitType


class Symbols(Enum):
    Variable = "Variable"
    Function = "Function"
    Type = "Type"
    TBD = "TBD"


class Symbol:
    def __init__(self, name, symbol_type):
        self._name = name
        self._symbol_type = symbol_type

    @property
    def symbol_type(self):
        return self._symbol_type

    @property
    def name(self):
        return self._name

    def __str__(self):
        return f"{self.name, self.symbol_type.name}"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return isinstance(other, Symbol) and self.name == other.name and self.symbol_type == other.symbol_type

    def __hash__(self):
        return hash((self.name, self.symbol_type))


class TBDSymbol(Symbol):

    def __init__(self, name):
        super().__init__(name, Symbols.TBD)


class VarSymbol(Symbol):
    def __init__(self, name: str, var_type: Type | StructureType | FunctionSignature | FunctionOverloadType, init_expr: 'ASTNode'=None):
        super().__init__(name, Symbols.Variable)
        self.init_expr = init_expr
        self.var_type = var_type

class TypeSymbol(Symbol):
    def __init__(self, name, type_def: StructureType=None, type_def_ast: 'TypeDefNode'=None, is_var=False):
        super().__init__(name, Symbols.Type)
        self.type_def = type_def or Type(name)
        self.type_def_ast = type_def_ast
        self.is_var = is_var


@dataclass
class FunctionOverload:
    signature: FunctionSignature
    func_def_ast: 'FuncDefNode'
    native_call: Any

    def __eq__(self, other):
        return type(self) == type(other) and self.signature.args == other.signature.args

    def __hash__(self):
        return hash(self.signature)


class FunctionSymbol(Symbol):
    def __init__(self, name, signature: FunctionSignature, func_def: 'FuncDefNode'=None, native_call=None, belong_to_trait=False):
        super().__init__(name, Symbols.Function)
        self.signature: FunctionSignature = signature
        self.func_def = func_def
        self.native_call = native_call
        self.belong_to_trait = belong_to_trait

    def __eq__(self, other):
        return isinstance(other, FunctionSymbol) and self.name == other.name and self.args_type == other.args_type

    def to_overload(self) -> FunctionOverload:
        return FunctionOverload(self.signature, self.func_def, self.native_call)


class FunctionOverloadSymbol(FunctionSymbol):

    def __init__(self, name: str):
        super().__init__(name, Symbols.Function)
        self.overloads: Set[FunctionOverload] = set()

    def get_overloads(self, args: Tuple[Type|FunctionSignature, ...]) -> Optional[FunctionOverload]:
        for overload in self.overloads:
            if overload.signature.args == args:
                return overload
        return None


class TraitSymbol(Symbol):

    def __init__(self, name: str, type_var_name: str, functions=None):
        super().__init__(name, Symbols.Variable)
        self.type_var_name = type_var_name
        self.functions: Dict[str, FunctionSignature] = (functions or {})

    def add_function(self, name, function: FunctionSignature):
        function.is_trait_function = True
        self.functions[name] = function