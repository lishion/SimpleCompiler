from typing import Dict
from parser.symbol_type import TypeRef, FunctionTypeRef, TraitRef, TypeVar
from parser.visitor.utils import type_constraint_validate, bind_type
from parser.scope import TraitImpls

class TypeBinder:
    def __init__(self, trait_impls: 'TraitImpls'):
        self._trait_impls = trait_impls
        self._binds: Dict[TypeVar, TypeRef|TypeVar] = {}

    def resolve(self, defined_type: TypeRef|TypeVar, real_type: TypeRef|TypeVar):
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

    def bind[T: TypeRef|FunctionTypeRef|TraitRef](self, type_ref: TypeRef|FunctionTypeRef|TraitRef) -> T:
        """
        bind type according to resolve method
        give T=Int, type_ref = A<B<T>> then output is A<B<Int>>
        :param type_ref: type need to bind
        :return: type after bind
        """
        return bind_type(type_ref, self._binds)

    def _resolve_type(self, etype: TypeRef|TypeVar, rtype: TypeRef|TypeVar):
        if TypeVar.is_a_var(etype):
            if exists_bind := self._binds.get(etype):
                if exists_bind == rtype:
                    return
                else:
                    raise TypeError(
                        f"type {etype.name} is already bind to {exists_bind} and can not bind to {rtype} again")
            for constraint in etype.constraints:
                type_constraint_validate(rtype, constraint, self._trait_impls)
            self._binds[etype] = rtype
        else:
            if etype.name != rtype.name:
                raise TypeError(f"expect type {etype.name} but got {rtype.name}")
            for et, rt in zip(etype.parameters, rtype.parameters):
                self._resolve_type(et, rt)

    def get_binds(self):
        return self._binds
