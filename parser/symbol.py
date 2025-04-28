from typing import Optional
from enum import Enum

class Symbols(Enum):
    Variable = "Variable"
    Function = "Function"
    Type = "Type"


class Symbol:
    def __init__(self, name, symbol_type: Symbols):
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


class VarSymbol(Symbol):
    def __init__(self, name: str, type_name: str, var_type: 'TypeDefNode'=None, init_expr: 'ASTNode'=None):
        super().__init__(name, Symbols.Variable)
        self.init_expr = init_expr
        self.var_type = var_type
        self.type_name = type_name

class TypeSymbol(Symbol):
    def __init__(self, name, type_def: 'TypeDefNode'=None):
        super().__init__(name, Symbols.Type)
        self._type_def = type_def

class BuildInTypeDefNode(TypeSymbol):
    def __init__(self, name):
        super().__init__(name,None)

class FunctionSymbol(Symbol):
    def __init__(self, name, args_type=tuple(), return_type=None, func_def: 'FuncDefNode'=None, native_call=None):
        super().__init__(name, Symbols.Function)
        self.args_type: tuple[TypeSymbol] = args_type
        self.return_type: Optional[TypeSymbol] = return_type
        self.func_def = func_def
        self.native_call = native_call

    def __eq__(self, other):
        return isinstance(other, FunctionSymbol) and self.name == other.name and self.args_type == other.args_type
