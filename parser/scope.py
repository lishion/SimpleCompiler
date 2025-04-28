from typing import Dict, Optional, List
from parser.symbol import Symbol, Symbols, FunctionSymbol


class Scope:

    UNDEFINED = None

    def __init__(self):
        self.parent: Optional['Scope'] = None
        self.symbols: Dict[str, Symbol|List[Symbol]] = {}
        self.child: Optional['Scope'] = None

    def lookup(self, name) -> Optional[Symbol|List[Symbol]]:
        s = self.symbols.get(name)
        if s:
            return s
        if not self.parent:
            return None
        return self.parent.lookup(name)

    def exists(self, symbol: Symbol) -> bool:
        s = self.symbols.get(symbol.name)
        return symbol == s

    def add(self, symbol: Symbol):
        if isinstance(symbol, FunctionSymbol):
            exists_functions = self.symbols.get(symbol.name, [])
            for exists_symbol in exists_functions:
                if exists_symbol == symbol:
                    raise ValueError(f'function {symbol.name} with parameter type ({",".join(symbol.args_type)}) already exists')
            self.symbols[symbol.name] = exists_functions + [symbol]
        else:
            if self.exists(symbol):
                raise ValueError(f"{symbol.symbol_type.name} {symbol.name} already exists")
            else:
                self.symbols[symbol.name] = symbol

    def find_parent_func(self) -> Optional[FunctionSymbol]:
        parent = self.parent
        while parent:
            if type(parent) == FunctionSymbol:
                return parent
            parent = parent.parent
        return None

    def __str__(self):
        return str(list(self.symbols.values()))

    def __repr__(self):
        return self.__str__()



GLOBAL_SCOPE = Scope()

# GLOBAL_SCOPE.set("print", print)


class ScopeManager:

    def __init__(self, global_scope: Scope):
        self.global_scope = global_scope
        self.current_scope: Scope = global_scope

    def enter(self) -> Scope:
        current = self.current_scope
        self.current_scope = Scope()
        self.current_scope.parent = current
        current.child = self.current_scope
        return self.current_scope

    def exit(self) -> Scope:
        self.current_scope = self.current_scope.parent
        return self.current_scope

    def ensure_not_exists(self, symbol: Symbol):
        if self.current_scope.exists(symbol):
            if isinstance(symbol, FunctionSymbol):
                raise ValueError(f"function {symbol.name} with args type ({','.join(symbol.args_type)}) already exists")
            else:
                raise ValueError(f"{symbol.symbol_type.name} {symbol.name} already exists")

    @property
    def current(self) -> Scope:
        return self.current_scope

    def show(self):
        def helper(scope: Scope, level: int=0):
            print(' ' * level, '---start---' )
            print(' ' * level, scope)
            if scope.child is not None:
                helper(scope.child, level + 1)
            print(' ' * level, '---end---')
        helper(self.global_scope)

    def add(self, symbol: Symbol):
        self.current_scope.add(symbol)

    def new_scope(self):
        return self

    def lookup(self, name) -> Optional[Symbol]:
        return self.current_scope.lookup(name)

    def __enter__(self):
        return self.enter()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.exit()

SCOPE_MANAGER = ScopeManager(GLOBAL_SCOPE)