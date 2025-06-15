from typing import List, Any, Callable, Dict, Iterable

from parser.node import TypeConstraint, TypeVarNode, TraitFunctionNode, FunctionDefNode, TraitConstraintNode
from parser.node import TypeInstance
from parser.scope import Scope, TraitImpls, ScopeManager
from parser.symbol_type import TraitRef, TypeRef, StructTypeRef, PrimitiveType, StructType, FunctionTypeRef, TraitImpl
from parser.visitor.visitor import Visitor


def visit_all(asts, visitor: Visitor):
    for ast in asts:
        if isinstance(ast, tuple) or isinstance(ast, list):
            for x in ast:
                x.accept(visitor)
        else:
            ast.accept(visitor)

def get_type_ref(ast: 'TypeInstance', type_var_names: Dict[str, TypeRef]=None) -> TypeRef:
    type_var_names = type_var_names or dict()
    def helper(type_instance: TypeInstance) -> TypeRef:
        if isinstance(type_instance, TraitConstraintNode):
            raise Exception("impl trait can only be used to return type")
        ref = TypeRef(type_instance.name)
        ref.constraints = param_type.constraints if (param_type := type_var_names.get(type_instance.name)) else []
        ref.is_var = type_instance.name in type_var_names
        ref.parameters = [helper(param) for param in type_instance.parameters]
        return ref
    return helper(ast)

def get_return_type_ref(ast: 'TypeInstance', type_var_names: Dict[str, TypeRef]=None, function_name:str=None):
    type_var_names = type_var_names or dict()
    indexer = {"val": 1}

    def helper(type_instance: TypeInstance | TraitConstraintNode) -> TypeRef:
        # for return a trait constraint type
        # def a() -> impl Into<String>
        # `impl Into<String>` will be compiled to an anonymous type function_name#T#{i-th of impl constraint}
        if isinstance(type_instance, TraitConstraintNode):
            type_name = function_name + f"#T#{indexer['val']}"
            indexer['val'] += 1
            ref = TypeRef(type_name)
            ref.constraints = [get_trait_ref(trait) for trait in type_instance.traits]
            ref.is_var = True
            ref.parameters = []
        else:
            ref = TypeRef(type_instance.name)
            ref.constraints = param_type.constraints if (param_type := type_var_names.get(type_instance.name)) else []
            ref.is_var = type_instance.name in type_var_names
            ref.parameters = [helper(param) for param in type_instance.parameters]
        return ref

    return helper(ast)

def get_func_type_ref(trait_function_node: TraitFunctionNode|FunctionDefNode, type_var_names: Dict[str, TypeRef]=None) -> FunctionTypeRef:
    type_var_names = type_var_names or dict()
    return FunctionTypeRef(
        name=trait_function_node.name.string,
        args=[get_type_ref(arg.var_type, type_var_names) for arg in trait_function_node.args],
        return_type=get_return_type_ref(trait_function_node.return_type, type_var_names=type_var_names, function_name=trait_function_node.name.string),
        type_parameters=[type_var_names.get(arg.var_type.name) for arg in trait_function_node.args if arg.var_type.name in type_var_names]
    )

def get_trait_ref(ast: 'TypeConstraint', type_var_names: Dict[str, TypeRef]=None) -> TraitRef:
    trait_ref = TraitRef(ast.trait.name)
    trait_ref.parameters = [get_type_ref(param, type_var_names) for param in ast.parameters]
    return trait_ref


def get_type_ref_from_type_var(ast: 'TypeVarNode') -> TypeRef:
    name = ast.name.string
    constraints = ast.constraints
    return TypeRef.type_var(name, mapper(constraints, get_trait_ref))


def to_lookup[K, V](obj: List[K], key_mapper: Callable[[K], V]) -> Dict[V, K]:
    return {key_mapper(k): k for k in obj}

def type_constraint_validate(type_ref: TypeRef, constraints: List[TraitRef]|TraitRef|TypeRef, trait_impls: TraitImpls):
    if isinstance(constraints, TypeRef) and type_ref != constraints:
        raise TypeError(f"return type {type_ref} does not match type {constraints}")
    def verify_constraint(ref1: TypeRef, ref2: TypeRef):
        if ref1.is_var:
            if ref1.constraints != ref2.constraints:
                raise TypeError(f"constraint not match {ref1.constraints} {ref2.constraints}")
        else:
            for param1, para2 in zip(ref1.parameters, ref2.parameters):
                verify_constraint(param1, para2)
    if not isinstance(constraints, list):
        constraints = [constraints]
    for constraint in constraints:
        if type_ref.is_var:
            if constraint not in type_ref.constraints:
                raise TypeError(f"Type {type_ref.name}: {type_ref.constraints} does not match constraint {constraint}")
            return False
        impl = trait_impls.get_impl(type_ref, constraint)
        if not impl:
            raise TypeError(f"{type_ref} is not implemented trait {constraint}")
        verify_constraint(type_ref, impl.target_type)
    return None




# def map_filter[K, V, C](iterable: Iterable[K], mapper:Callable[[K], V], _filter: Callable[[K], bool]=None, collector:Callable[[Iterable[V]], C]=list) -> C:
#     _filter = _filter or (lambda _: True)
#     return collector((mapper(x) for x in iterable if _filter(x)))

def mapper[K, V](iterable: Iterable[K], _map:Callable[[K], V]) -> List[V]:
    return [_map(x) for x in iterable]

def de_ref(type_ref: TypeRef, scope: Scope) -> TypeRef:
    if type_ref.is_primitive_type:
        return type_ref
    else:
        struct_type_ref = scope.lookup_type(type_ref.name).define
        type_binds = {btype.name: dtype for btype, dtype in zip(struct_type_ref.parameters, type_ref.parameters)}
        type_ref.struct_ref = StructTypeRef(type_ref.name, fields={name: type_binds.get(field.name, field) for name, field in struct_type_ref.fields.items()})
        return type_ref


def get_struct_ref(ref: TypeRef, scope: Scope) -> TypeRef:
    if not ref.struct_ref:
        symbol = scope.lookup_type(ref.name)
        assert symbol
        assert symbol.define
        if not isinstance(symbol.define, StructTypeRef):
            raise TypeError(f"Type {ref.name} is not a struct")
        ref.struct_ref = symbol.define
    return ref

def bind_type[T: TypeRef|FunctionTypeRef](type_ref: T, binds: Dict[str, TypeRef]) -> T:
    """
    bind type according to resolve method
    give T=Int, type_ref = A<B<T>> then output is A<B<Int>>
    :param binds:
    :param type_ref: type need to bind
    :return: type after bind
    """

    def _bind(ref: TypeRef):
        if (deref := binds.get(ref.name)) is not None:
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

    if isinstance(type_ref, TypeRef):
        return _bind(type_ref)
    return FunctionTypeRef(
        type_ref.name,
        args=mapper(type_ref.args, _bind),
        return_type=_bind(type_ref.return_type)
    )

def equal_without_constraint(ref1: TypeRef, ref2: TypeRef) -> bool:
    if ref1.is_var and ref2.is_var:
        return True
    elif ref1.name == ref2.name:
        return all(equal_without_constraint(r1, r2) for r1, r2 in zip(ref1.parameters, ref2.parameters))
    return False

def validate_return_type(real_type: TypeRef, expect_type: TypeRef, trait_impl: TraitImpls):
    if "#" in expect_type.name:
        type_constraint_validate(real_type, expect_type.constraints, trait_impl)
        return
    if expect_type.is_var and real_type != expect_type:
        raise TypeError(f"expect {expect_type.name} but got {real_type.name}")
    if real_type.name != expect_type.name:
        raise TypeError(f"Type {real_type.name} is not {expect_type.name}")
    for r1, r2 in zip(real_type.parameters, expect_type.parameters):
        validate_return_type(r1, r2, trait_impl)
