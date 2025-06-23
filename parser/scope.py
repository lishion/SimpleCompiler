import copy
from typing import Optional, Dict

from error.exception import DuplicateDefineError
from parser.symbol import *
from parser.symbol_type import TraitImpl, TraitRef



class Scope:

    UNDEFINED = None

    def __init__(self):
        self.parent: Optional['Scope'] = None
        self.symbols: Dict[str, VarSymbol] = {}
        self.traits: Dict[str, TraitSymbol] = {}
        self.types: Dict[str, TypeSymbol] = {}
        self.generic_symbols: Dict[str, GenericParamSymbol] = {}
        self.child: Optional['Scope'] = None
        self.trait_impls: List[TraitTypeRef] = []

    def lookup_var(self, name: str) -> Optional[VarSymbol]:
        s = self.symbols.get(name)
        if s:
            return s
        if not self.parent:
            return None
        return self.parent.lookup_var(name)

    def lookup_traits(self, name: str) -> Optional[TraitSymbol]:
        s = self.traits.get(name)
        if s:
            return s
        if not self.parent:
            return None
        return self.parent.lookup_traits(name)

    def lookup_type(self, name: str) -> Optional[TypeSymbol|GenericParamSymbol]:
        s = self.generic_symbols.get(name, self.types.get(name))
        if s:
            return s
        if not self.parent:
            return None
        return self.parent.lookup_type(name)

    def exists(self, symbol: str) -> bool:
        s = self.symbols.get(symbol)
        return symbol == s

    def add_var(self, symbol: VarSymbol | FunctionSymbol):
        defined_symbol = self.symbols.get(symbol.name)
        if defined_symbol:
                raise DuplicateDefineError(
                    f'"{symbol.name}" already exists')
        self.symbols[symbol.name] = symbol

    def add_type(self, symbol: TypeSymbol|GenericParamSymbol):
        defined_symbol = self.types.get(symbol.name)
        if defined_symbol:
            raise DuplicateDefineError(
                f'"{symbol.name}" already exists')
        self.types[symbol.name] = symbol


    def impl_trait(self, trait_type: TraitTypeRef):
        if self.parent:
            self.parent.impl_trait(trait_type)
        else:
            self.trait_impls.append(trait_type)

    # def get_impl_by_target(self, target):
    #     if self.parent:
    #         return self.parent.get_impl_by_target(target)
    #     else:
    #         return self.trait_impls.get_impls(target)


    def __str__(self):
        return str(list(self.symbols.values())) + " " + str(list(self.types.values())) + " " + str(list(self.traits.values()))

    def __repr__(self):
        return self.__str__()


class ScopeManager:

    def __init__(self, global_scope: Scope=None):
        self.global_scope = global_scope or Scope()
        self.current_scope: Scope = self.global_scope
        self.trait_impls: List[TraitTypeRef] = []

    def enter(self) -> Scope:
        current = self.current_scope
        self.current_scope = Scope()
        self.current_scope.parent = current
        current.child = self.current_scope
        return self.current_scope

    def exit(self) -> Scope:
        self.current_scope = self.current_scope.parent
        return self.current_scope

    def show(self):
        def helper(scope: Scope, level: int=0):
            print(' ' * level, '---start---' )
            print(' ' * level, scope)
            if scope.child is not None:
                helper(scope.child, level + 1)
            print(' ' * level, '---end---')
        helper(self.global_scope)

    def new_scope(self):
        return self

    def lookup_var(self, name) -> Optional[VarSymbol|FunctionSymbol]:
        return self.current_scope.lookup_var(name)

    def add_trait(self, trait: TraitSymbol):
        if trait.name in self.global_scope.traits:
            raise DuplicateDefineError(
                f'A trait with name `{trait.name}` already exists')
        self.global_scope.traits[trait.name] = trait

    def add_type(self, type_symbol: TypeSymbol):
        self.current_scope.add_type(type_symbol)

    def add_generic_var(self, type_symbol: GenericParamSymbol):
        self.current_scope.add_type(type_symbol)


    def add_symbol(self, symbol: TypeSymbol | FunctionSymbol | VarSymbol | TraitSymbol | GenericParamSymbol, ast=None):
        try:
            if type(symbol) in (VarSymbol, FunctionSymbol):
                self.current_scope.add_var(symbol)
            elif type(symbol) is TypeSymbol:
                self.current_scope.add_type(symbol)
            elif type(symbol) is TraitSymbol:
                self.add_trait(symbol)
            elif isinstance(symbol, GenericParamSymbol):
                self.add_generic_var(symbol)
            else:
                #utils.died_branch()
                assert False
        except DuplicateDefineError as e:
            message = e.message
            raise DuplicateDefineError((message + "\n"))

    def lookup_var(self, name) -> Optional[VarSymbol]:
        return self.current_scope.lookup_var(name)

    def lookup_traits(self, name) -> Optional[TraitSymbol]:
        return self.current_scope.lookup_traits(name)

    def lookup_type(self, name) -> Optional[TypeSymbol]:
        return self.current_scope.lookup_type(name)

    def __enter__(self):
        return self.enter()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.exit()
        return False

class TraitImpls:

    def __init__(self):
        self.trait_impls: List[TraitImpl] = []

    def get_impl(self, type_ref: TypeRef, trait_ref: TraitRef) -> Optional[TraitImpl]:
        for impl in self.trait_impls:
            if type_ref == impl.target_type and trait_ref == impl.trait:
                return impl
        return None

    def _is_type_match(self, r1: TypeRef|TypeVar, r2: TypeRef|TypeVar) -> bool:
        if r2.is_var:
            if not r2.constraints:
                return True
            else:
                for constraint in r2.constraints:
                    if not self.get_impl(r1, constraint):
                        return False
        if r1.name != r2.name:
            return False
        elif r1.parameters:
            if len(r1.parameters) != len(r2.parameters):
                return False
            for r1, r2 in zip(r1.parameters, r2.parameters):
                if not self._is_type_match(r1, r2):
                    return False
        return True

    def get_impl_by_type(self, type_ref: TypeRef) -> List[TraitImpl]:
        from parser.visitor.type_binder import TypeBinder
        res = []
        for impl in self.trait_impls:
            if self._is_type_match(type_ref, impl.target_type):
                type_binder = TypeBinder(self)
                type_binder.resolve(impl.target_type,  type_ref)
                bind_trait = type_binder.bind(impl.trait)
                res_params = []
                for p in impl.type_parameters:
                    if bind_type := type_binder.get_binds().get(p):
                        if bind_type.is_var:
                            res_params.append(bind_type)
                    else:
                        res_params.append(p)
                bind_impl = TraitImpl(
                    bind_trait,
                    type_ref,
                    res_params
                )
                for func_name, func in impl.functions.items():
                    f = type_binder.bind(func)
                    f.association_impl = bind_impl
                    bind_impl.functions[func_name] = f
                res.append(bind_impl)
        return res

    def add_impl(self, impl: TraitImpl):
        self.trait_impls.append(impl)