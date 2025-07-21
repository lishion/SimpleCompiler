from typing import Dict
from parser.symbol_type import TypeRef, FunctionTypeRef, TraitRef, TypeVar, TraitImpl, ResolvedFunctionRef

from parser.scope import TraitImpls

class TypeBinder:
    def __init__(self, trait_impls: 'TraitImpls', binds: Dict[TypeVar, TypeRef]=None):
        self._trait_impls = trait_impls
        self._binds: Dict[TypeVar, TypeRef|TypeVar] = binds or {}

    def resolve(self, defined_type: TypeRef|TypeVar|TraitRef, real_type: TypeRef|TypeVar|TraitRef):
        """
        given defined_type like A<B<T1, T2>> and real_type A<B<String, Int>>
        bind String to T1 and Int to T2

        TypeError will rase if there is a conflict like defined_type = A<B<T, T>> and real_type A<B<String, Int>> \
        can not bind String and Int to T at same time

        :param defined_type:
        :param real_type:
        :return: None
        """
        return self._resolve_type(defined_type, real_type)

    def bind[T: TypeRef|FunctionTypeRef|TraitRef|ResolvedFunctionRef](self, type_ref: T) -> T:
        from parser.visitor.utils import bind_type
        """
        bind type according to resolve method
        give T=Int, type_ref = A<B<T>> then output is A<B<Int>>
        :param type_ref: type need to bind
        :return: type after bind
        """
        return bind_type(type_ref, self._binds)

    def _resolve_type(self, dtype: TypeRef | TypeVar | TraitRef, rtype: TypeRef | TypeVar | TraitRef):
        """
        :param dtype: defined_type
        :param rtype: real_type
        :return:
        """
        if TypeVar.is_a_var(dtype):
            if exists_bind := self._binds.get(dtype):
                if exists_bind == rtype:
                    return
                else:
                    raise TypeError(
                        f"type {dtype.name} is already bind to {exists_bind} and can not bind to {rtype} again")
            # 如果定义的类型有约束条件，那么还需要验证真实类型是否满足这个约束条件，否则无法绑定
            for constraint in dtype.constraints:
                if not self._trait_impls.is_type_match(rtype, constraint):
                    raise TypeError(f"can not bind {rtype} to {dtype.name} because constraint {constraint} is not meet")
            self._binds[dtype] = rtype
        else:
            if dtype.name.lower() == "any" or rtype.name.lower() == "any":
                return
            if dtype.name != rtype.name:
                raise TypeError(f"expect type {dtype.name} but got {rtype.name}")
            for et, rt in zip(dtype.parameters, rtype.parameters):
                self._resolve_type(et, rt)

    def get_binds(self):
        return self._binds

    def bind_impl(self, impl: 'TraitImpl'):
        bind_trait = self.bind(impl.trait)
        bind_target_type = self.bind(impl.target_type)
        res_params = []
        for p in impl.type_parameters:
            if _bind_type := self.get_binds().get(p):
                if _bind_type.is_var:
                    res_params.append(_bind_type)
            else:
                res_params.append(p)
        bind_impl = TraitImpl(
            bind_trait,
            bind_target_type,
            res_params
        )
        for func_name, func in impl.functions.items():
            f = self.bind(func)
            f.association_impl = bind_impl
            bind_impl.functions[func_name] = f
        bind_impl.binds = self.get_binds()
        return bind_impl

    def resolve_impl_and_bind(self, impl: TraitImpl, real_trait: TraitRef|None=None, real_target: TypeRef|None=None):
        if not real_trait and not real_target:
            raise TypeError("real_trait and real_target is both None")
        real_trait and self.resolve(impl.trait, real_trait)
        real_target and self.resolve(impl.target_type, real_target)
        return self.bind_impl(impl)