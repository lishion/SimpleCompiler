import copy
from typing import List, Callable, Dict, Iterable, Tuple

from parser.node import TypeInstance,TypeConstraint, TypeVarNode, TraitFunctionNode, FunctionDefNode, TraitConstraintNode
from parser.symbol_type import TraitRef, TypeRef, StructTypeRef, PrimitiveType, FunctionTypeRef, TypeVar, TraitImpl, \
    ResolvedFunctionRef
from parser.visitor.type_binder import TypeBinder
from parser.visitor.visitor import Visitor
from parser.scope import Scope, TraitImpls

def visit_all(asts, visitor: Visitor):
    for ast in asts:
        if isinstance(ast, tuple) or isinstance(ast, list):
            for x in ast:
                x.accept(visitor)
        else:
            ast.accept(visitor)

def get_type_ref(ast: 'TypeInstance', type_var_names: Dict[str, TypeVar|TypeRef]=None) -> TypeRef|TypeVar:
    type_var_names = type_var_names or dict()
    def helper(type_instance: TypeInstance) -> TypeRef|TypeVar:
        if isinstance(type_instance, TraitConstraintNode):
            return TypeVar.create("ANON_TYPE_ARG_VAR", [get_trait_ref(trait, type_var_names) for trait in type_instance.traits])
        if type_var := type_var_names.get(type_instance.name):
            return type_var
        ref = TypeRef(type_instance.name)
        ref.parameters = [helper(param) for param in type_instance.parameters]
        return ref
    return helper(ast)

def get_return_type_ref(ast: 'TypeInstance', type_var_names: Dict[str, TypeRef]=None, function_name:str=None):
    type_var_names = type_var_names or dict()
    if isinstance(ast, TraitConstraintNode):
        return TypeVar.create("ANON_TYPE_VAR", [get_trait_ref(trait) for trait in ast.traits])
    else:
        return get_type_ref(ast, type_var_names)


def get_function_ref(trait_function_node: TraitFunctionNode | FunctionDefNode, type_var_names: Dict[str, TypeVar|TypeRef]=None) -> FunctionTypeRef:
    type_var_names = type_var_names or dict()

    arg_types = [get_type_ref(arg.var_type, type_var_names) for arg in trait_function_node.args]

    return FunctionTypeRef(
        name=trait_function_node.name.string,
        args=arg_types,
        return_type=get_return_type_ref(trait_function_node.return_type, type_var_names=type_var_names, function_name=trait_function_node.name.string),
        type_parameters=[arg for arg in arg_types if isinstance(arg, TypeVar)],
    )

def get_trait_ref(ast: 'TypeConstraint', type_var_names: Dict[str, TypeRef|TypeVar]=None) -> TraitRef:
    trait_ref = TraitRef(ast.trait.name)
    trait_ref.parameters = [get_type_ref(param, type_var_names) for param in ast.parameters]
    return trait_ref


def get_type_ref_from_type_var(ast: 'TypeVarNode') -> TypeVar:
    return TypeVar.create(ast.name.string, mapper(ast.constraints, get_trait_ref))

def identity[U](u: U) -> U:
    return u


def to_lookup[K, V](obj: List[K], key_mapper: Callable[[K], V]=identity) -> Dict[V, K]:
    return {key_mapper(k): k for k in obj}

# def type_constraint_validate(type_ref: TypeRef|TypeVar, constraints: List[TraitRef]|TraitRef|TypeRef|TypeVar, trait_impls: TraitImpls):
#     if isinstance(constraints, TypeRef) and type_ref != constraints:
#         raise TypeError(f"return type {type_ref} does not match type {constraints}")
#     def verify_constraint(ref1: TypeRef|TypeVar, ref2: TypeRef|TypeVar):
#         if TypeVar.is_a_var(ref1):
#             if ref1.constraints != ref2.constraints:
#                 raise TypeError(f"constraint not match {ref1.constraints} {ref2.constraints}")
#         else:
#             for param1, para2 in zip(ref1.parameters, ref2.parameters):
#                 verify_constraint(param1, para2)
#     if not isinstance(constraints, list):
#         constraints = [constraints]
#     for constraint in constraints:
#         if TypeVar.is_a_var(type_ref):
#             if constraint not in type_ref.constraints:
#                 raise TypeError(f"Type {type_ref.name}: {type_ref.constraints} does not match constraint {constraint}")
#             return False
#         impl = trait_impls.get_impl(type_ref, constraint)
#         if not impl:
#             raise TypeError(f"{type_ref} is not implemented trait {constraint}")
#         verify_constraint(type_ref, impl.target_type)
#     return None




# def map_filter[K, V, C](iterable: Iterable[K], mapper:Callable[[K], V], _filter: Callable[[K], bool]=None, collector:Callable[[Iterable[V]], C]=list) -> C:
#     _filter = _filter or (lambda _: True)
#     return collector((mapper(x) for x in iterable if _filter(x)))

def mapper[K, V](iterable: Iterable[K], _map:Callable[[K], V]) -> List[V]:
    return [_map(x) for x in iterable]

def de_ref(type_ref: TypeRef|TypeVar, scope: Scope) -> TypeRef|TypeVar:
    if isinstance(type_ref, TypeVar):
        return type_ref
    if type_ref.is_primitive_type or isinstance(type_ref, PrimitiveType):
        return type_ref
    else:
        struct_type_ref = scope.lookup_type(type_ref.name).define
        type_binds = {btype: dtype for btype, dtype in zip(struct_type_ref.parameters, type_ref.parameters)}
        type_ref.struct_ref = StructTypeRef(type_ref.name, fields={name: bind_type(field, type_binds) for name, field in struct_type_ref.fields.items()})
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

def bind_type[T: TypeRef|FunctionTypeRef|TraitRef|ResolvedFunctionRef](type_ref: T, binds: Dict[TypeVar, TypeRef]) -> T:
    """
    bind type according to binds
    give T=Int, type_ref = A<B<T>> then output is A<B<Int>>
    :param binds: type var name: real type mapping
    :param type_ref: type need to bind
    :return: type after bind
    """

    def _bind(ref: TypeRef|TypeVar):
        if TypeVar.is_a_var(ref):
            return binds.get(ref, ref)
        if ref.is_primitive_type:
            return ref
        elif ref.parameters:
            new_ref = TypeRef(
                ref.name,
                parameters=[_bind(r) for r in ref.parameters]
            )
            return new_ref
        else:
            return ref

    if isinstance(type_ref, TypeRef) or isinstance(type_ref, TypeVar):
        return _bind(type_ref)
    if isinstance(type_ref, ResolvedFunctionRef):
        rfunc_ref = copy.copy(type_ref)
        rfunc_ref.args = mapper(type_ref.args, _bind)
        rfunc_ref.return_type = _bind(type_ref.return_type)
        rfunc_ref.association_trait = rfunc_ref.association_trait and bind_type(rfunc_ref.association_trait, binds)
        rfunc_ref.association_type = rfunc_ref.association_type and bind_type(rfunc_ref.association_type, binds)
        return rfunc_ref
    elif isinstance(type_ref, TraitRef):
        return TraitRef(
            name=type_ref.name,
            parameters=[_bind(p) for p in type_ref.parameters]
        )
    func_ref = copy.copy(type_ref)
    func_ref.args = mapper(type_ref.args, _bind)
    func_ref.return_type = _bind(type_ref.return_type)
    return func_ref

def equal_without_constraint(ref1: TypeRef|TypeVar, ref2: TypeRef|TypeVar) -> bool:
    if ref1.is_var and ref2.is_var:
        return True
    elif ref1.name == ref2.name:
        return all(equal_without_constraint(r1, r2) for r1, r2 in zip(ref1.parameters, ref2.parameters))
    return False

def validate_return_type(real_type: TypeRef|TypeVar, expect_type: TypeRef|TypeVar, trait_impl: TraitImpls):
    if expect_type.name == "ANON_TYPE_VAR":
        #type_constraint_validate(real_type, expect_type.constraints, trait_impl)
        if not trait_impl.is_type_match(real_type, expect_type):
            raise TypeError(f"expect {expect_type.name} but got {real_type.name}")
        return
    elif expect_type.is_var:
        if real_type != expect_type:
            raise TypeError(f"expect {expect_type.name} but got {real_type.name}")
        else:
            return
    if real_type.name != expect_type.name:
        raise TypeError(f"Type {real_type.name} is not {expect_type.name}")
    for r1, r2 in zip(real_type.parameters, expect_type.parameters):
        validate_return_type(r1, r2, trait_impl)

def get_type_id(type_ref: TypeRef|TraitRef):
    if TypeVar.is_a_var(type_ref):
        return "0DYN0"
    return str(type_ref).replace("<", "_p_").replace(">", "_q_").replace(",", "__").replace(" ", "")

def get_trait_function_name(trait_ref: TraitRef, type_ref: TypeRef, function_name: str) -> str:
    return f"{get_type_id(trait_ref)}_for_{get_type_id(type_ref)}___{function_name}"

def get_type_name(ref: TypeRef|TypeVar) -> str:
    return ref.name

def resolve_type_binds(binds: Dict[TypeVar, TypeRef|TypeVar], parent_binds: Dict[TypeVar, TypeRef|TypeVar]) -> Dict[TypeVar, TypeRef|TypeVar]:
    #print(binds, parent_binds)
    return {type_var: parent_binds.get(bind_type, bind_type) if bind_type.is_var else bind_type  for type_var, bind_type in binds.items()}

# def bind_impl(impl: TraitImpl, real_trait: TraitRef|None, real_target: TypeRef|None) -> TraitImpl:
#     if not real_trait and not real_target:
#         raise TypeError("real_trait and real_target is both None")
#     type_binder = TypeBinder(real_trait.name, real_target.name)


def is_dyn_dispatch(caller: TypeVar|TypeRef, args: Iterable[TypeVar|TypeRef]) -> bool:
    return any(TypeVar.is_a_var(arg) for arg in args) or TypeVar.is_a_var(caller)

# def create_dyn_object(type_ref: TypeRef|TypeVar, constraints: List['TraitRef']) -> TypeRef: