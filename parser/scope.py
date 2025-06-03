from typing import Dict, Optional, List
from collections import defaultdict
from error.exception import DuplicateDefineError
from parser.symbol import Symbol, FunctionSymbol, FunctionOverloadSymbol, VarSymbol, \
    TypeSymbol, TraitSymbol, TBDSymbol


class TraitImpls:

    def __init__(self):
        self.type_trait_lookup: Dict[str, Dict[str, List[FunctionSymbol]]] = defaultdict(lambda: defaultdict(list))

    def add_impls(self, target_type, trait, function:  FunctionSymbol):
        self.type_trait_lookup[target_type][trait].append(function)

    def get_impls(self, target_type):
        return self.type_trait_lookup.get(target_type)

class Scope:

    UNDEFINED = None

    def __init__(self):
        self.parent: Optional['Scope'] = None
        self.symbols: Dict[str, VarSymbol|TypeSymbol|FunctionOverloadSymbol] = {}
        self.traits: Dict[str, TraitSymbol] = {}
        self.types: Dict[str, TypeSymbol] = {}
        self.child: Optional['Scope'] = None
        self.trait_impls: TraitImpls = TraitImpls()
        self.outer_names = []
        self.current_names = []

    def lookup(self, name) -> Optional[VarSymbol|TypeSymbol|FunctionOverloadSymbol|TraitSymbol]:
        s = self.symbols.get(name)
        if s:
            return s
        if not self.parent:
            return None
        return self.parent.lookup(name)

    def add_type_var(self, type_var: TypeSymbol):
        self.types[type_var.name] = type_var

    def replace(self, name, symbol: VarSymbol|FunctionSymbol):
        assert name in self.symbols
        self.symbols[name] = symbol

    def lookup_traits(self, name) -> Optional[TraitSymbol]:
        s = self.traits.get(name)
        if s:
            return s
        if not self.parent:
            return None
        return self.parent.lookup_traits(name)

    def lookup_type(self, name) -> Optional[TypeSymbol]:
        s = self.types.get(name)
        if s:
            return s
        if not self.parent:
            return None
        return self.parent.lookup_type(name)

    def exists(self, symbol: Symbol) -> bool:
        s = self.symbols.get(symbol.name)
        return symbol == s

    def add(self, symbol: VarSymbol|TypeSymbol|FunctionSymbol|TBDSymbol):
        defined_symbol = self.symbols.get(symbol.name)
        if defined_symbol:
                raise DuplicateDefineError(
                    f'"{symbol.name}" already exists')
        self.symbols[symbol.name] = symbol
        self.current_names.append(symbol.name)

    def impl_trait(self, target_type: str, trait: str, function:  FunctionSymbol):
        if self.parent:
            self.parent.impl_trait(target_type, trait, function)
        else:
            self.trait_impls.add_impls(target_type, trait, function)

    def get_impl_by_target(self, target):
        if self.parent:
            return self.parent.get_impl_by_target(target)
        else:
            return self.trait_impls.get_impls(target)

    def find_parent_func(self) -> Optional[FunctionSymbol]:
        parent = self.parent
        while parent:
            if type(parent) is FunctionOverloadSymbol:
                return parent
            parent = parent.parent
        return None

    def __str__(self):
        return str(list(self.symbols.values()))

    def __repr__(self):
        return self.__str__()


class ScopeManager:

    def __init__(self, global_scope: Scope=None):
        self.global_scope = global_scope or Scope()
        self.current_scope: Scope = self.global_scope

    def enter(self) -> Scope:
        current = self.current_scope
        self.current_scope = Scope()
        self.current_scope.parent = current
        self.current_scope.outer_names = current.outer_names

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
                raise ValueError(f"{symbol.name} already exists")

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

    def add(self, symbol: VarSymbol|TypeSymbol|FunctionSymbol):
        self.current_scope.add(symbol)

    def new_scope(self):
        return self

    def lookup(self, name) -> Optional[Symbol]:
        return self.current_scope.lookup(name)

    def add_trait(self, trait: TraitSymbol):
        if trait.name in self.global_scope.traits:
            raise DuplicateDefineError(
                f'A trait with name `{trait.name}` already exists')
        self.global_scope.traits[trait.name] = trait

    def add_type(self, type_symbol: TypeSymbol):
        if type_symbol.name in self.global_scope.types:
            raise DuplicateDefineError(
                f'A type with name `{type_symbol.name}` already exists')
        self.global_scope.types[type_symbol.name] = type_symbol
        self.global_scope.current_names.append(type_symbol.name)

    def __enter__(self):
        return self.enter()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.exit()
        return False
