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

    def __copy__(self):
        return Scope(
            self.parent,
            self.symbols[:],
        )


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

    def lookup_type(self, name) -> Optional[TypeSymbol|GenericParamSymbol]:
        return self.current_scope.lookup_type(name)

    def __enter__(self):
        return self.enter()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.exit()
        return False

class TraitImpls:

    def __init__(self):
        self.trait_impls: List[TraitImpl] = []

    def get_impl(self, type_ref: TypeRef, trait_ref: TraitRef, need_bind=True) -> List[TraitImpl]:
        impls = []
        # type_ref: Box<String>
        # trait_ref: Trait1<T>
        # impl.trait = Trait1<String>
        for impl in self.trait_impls:
            # print(
            #     trait_ref.name, impl.trait.name
            # )
            # print(
            #     len(trait_ref.parameters), len(impl.trait.parameters)
            # )
            # print(
            #     trait_ref.parameters, impl.trait.parameters , [self.is_type_match(r1, r2) for r1, r2 in zip(trait_ref.parameters, impl.trait.parameters)]
            # )
            if (self.is_type_match(type_ref, impl.target_type)
                        and trait_ref.name == impl.trait.name
                        and len(trait_ref.parameters) == len(impl.trait.parameters)
                        #and all(self.is_type_match(r1, r2) for r1, r2 in zip(trait_ref.parameters, impl.trait.parameters) )
                        and all(self.is_type_match(r1, r2) for r1, r2 in zip(impl.trait.parameters, trait_ref.parameters) )
            ):
                impls.append(self.bind_impl(impl, real_target=type_ref, real_trait=trait_ref) if need_bind else impl)
        return impls

    def is_type_match(self, r1: TypeRef|TypeVar, r2: TypeRef|TypeVar|TraitRef) -> bool:
        """
        判断类型 r1 是否满足 r2 的约束，有以下几种情况：
        1. r1, r2 都为具体类型，则递归比较类型是否完全相同，例如: List<String> == List<String>, List<Int> != List<String>
        2. r1 为具体类型，r2 为类型变量。那么此时需要先看 r2 是否有约束:
            2.a 如果没有约束，则 r1 必定符合 r2。
            2.b 如果有约束，则判断 r1 是否满足约束
        3. r1, r2 都为类型变量。那么需要保证 r2 的约束在 r1 中都存在
        4. r1 为类型变量，r2 为具体类型。这种情况应该为固定 false，因为一个类型变量无论约束再多，都无法收束到一个具体类型

        impl <T> Read<T> for Int{
            def read() -> T{

            }
        }

        :param r1:
        :param r2:
        :return:
        """
        # support trait ref
        if isinstance(r2, TraitRef):
            # 名字不是必须的，只要有约束即可
            return self.is_type_match(r1, TypeVar.create("__", [r2]))
        # case 4
        if r1.is_var and not r2.is_var:
            return False
        if r2.is_var:
            # case 2.a
            if not r2.constraints:
                return True
            else:
                for constraint in r2.constraints:
                    # case 3
                    if r1.is_var:
                        if constraint not in r1.constraints:
                            return False
                    # case 2.b

                    elif not self.get_impl(r1, constraint, need_bind=False):
                        return False
        # case 1，如果类型名不同，那么肯定不满足约束
        elif r1.name != r2.name:
            return False
        # 递归比较
        elif r1.parameters:
            if len(r1.parameters) != len(r2.parameters):
                return False
            for r1, r2 in zip(r1.parameters, r2.parameters):
                if not self.is_type_match(r1, r2):
                    return False
        return True

    def bind_impl(self, impl: TraitImpl, real_trait: TraitRef|None=None, real_target: TypeRef|None=None):
        from parser.visitor.type_binder import TypeBinder
        return TypeBinder(self).resolve_impl_and_bind(impl, real_target=real_target, real_trait=real_trait)

    def get_impl_by_type(self, type_ref: TypeRef) -> List[TraitImpl]:
        return [self.bind_impl(impl, real_target=type_ref) for impl in self.trait_impls if self.is_type_match(type_ref, impl.target_type)]

    def get_impl_by_trait(self, trait_ref: TraitRef) -> List[TraitImpl]:
        impls = []
        for impl in self.trait_impls:
            if (trait_ref.name == impl.trait.name
                    and len(trait_ref.parameters) == len(impl.trait.parameters)
                    and all(self.is_type_match(r1, r2) for r1, r2 in zip(trait_ref.parameters, impl.trait.parameters))
            ):
                impls.append(self.bind_impl(impl, real_trait=trait_ref))
        return impls

    # def get_func_by_name(self, type_ref: TypeRef, func_name: str) -> List[FunctionTypeRef]:
    #     for impl in self.get_impl_by_type(type_ref):
    #         for func_name, func in impl.functions.items():
    #             compile_name = type_utils.get_trait_function_name(trait, expr_type, func_name)
    #             type_context = TypeContext(trait_impl=impl, function_name=compile_name, type_binds={})
    #             self.type_contexts.append(type_context)
    #             self.function_defs.append(self.visit_function_def(func.association_ast))
    #             self.type_contexts.pop(-1)
    #             self.meta_manager.get_or_create_meta(type_utils.get_type_id(expr_type)).vtable[func_name][
    #                 type_utils.get_type_id(trait)] = NameFunctionObject(compile_name, self.meta_manager.globals)

    def add_impl(self, impl: TraitImpl):
        self.trait_impls.append(impl)