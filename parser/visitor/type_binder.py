from typing import Dict

from parser.scope import TraitImpls
from parser.symbol_type import TypeRef
from parser.visitor.utils import type_constraint_validate


class TypeBinder:
    def __init__(self, trait_impls: TraitImpls):
        self._trait_impls = trait_impls
        self._binds: Dict[str, TypeRef] = {}

    def resolve(self, defined_type: TypeRef, real_type: TypeRef):
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

    def bind(self, type_ref):
        """
        bind type according to resolve method
        give T=Int, type_ref = A<B<T>> then output is A<B<Int>>
        :param type_ref: type need to bind
        :return: type after bind
        """
        def _bind(ref: TypeRef):
            if (deref := self._binds.get(ref.name)) is not None:
                return deref
            elif ref.is_primitive_type:
                return ref
            elif ref.parameters:
                new_ref = TypeRef(
                    ref.name,
                    parameters=[_bind(r) for r in ref.parameters]
                )
                return new_ref
            else:
                return ref
        return _bind(type_ref)

    def _resolve_type(self, etype: TypeRef, rtype: TypeRef):
        if etype.is_var:
            if exists_bind := self._binds.get(etype.name):
                if exists_bind == rtype:
                    return
                else:
                    raise TypeError(
                        f"type {etype.name} is already bind to {exists_bind} and can not bind to {rtype} again")
            for constraint in etype.constraints:
                type_constraint_validate(rtype, constraint, self._trait_impls)
            self._binds[etype.name] = rtype
        else:
            if etype.name != rtype.name:
                raise TypeError(f"expect type {etype.name} but got {rtype.name}")
            for et, rt in zip(etype.parameters, rtype.parameters):
                self._resolve_type(et, rt)

    def get_binds(self):
        return self._binds
