from array import ArrayType
from typing import Dict

from parser.symbol_type import StructTypeRef, TraitTypeRef, FunctionTypeRef, TypeRef, TraitImpl, TraitRef, \
    PrimitiveType, \
    StructType, MultiResolvedFunction, TypeVar
from parser.node import *
from parser.scope import ScopeManager, TraitImpls
from parser.symbol import TypeSymbol, TraitSymbol, GenericParamSymbol, FunctionSymbol, VarSymbol
from parser.visitor import utils
from parser.visitor.type_binder import TypeBinder
from parser.visitor.utils import type_constraint_validate, to_lookup, get_type_name
from copy import copy

class TypeDefVisitor(Visitor):

    def __init__(self, scope_manager: ScopeManager, trait_impls: TraitImpls):
        self.scope_manager = scope_manager
        self.trait_impls = trait_impls

    def add_self_type(self):
        self.scope_manager.add_symbol(TypeSymbol('Self', define=None, parameters={}))

    def add_type_param(self, name: str, type_var: TypeVar):
        self.scope_manager.add_symbol(GenericParamSymbol(name, type_var))

    def bind_scope(self, ast: 'ASTNode'):
        ast.scope = self.scope_manager.current_scope

    def visit_struct_def(self, node: 'StructDefNode'):
        self.bind_scope(node)
        parameters = [utils.get_type_ref_from_type_var(param) for param in node.name_and_param.parameters]
        parameters_lookup = to_lookup(parameters, lambda p: p.name)
        symbol = TypeSymbol(
            name=node.name_and_param.name,
            define=StructTypeRef(
                    node.name_and_param.name,
                    fields={field.string: utils.get_type_ref(type_instance, parameters_lookup) for field, type_instance in node.fields},
                    parameters=parameters,
            ),
            parameters=parameters,
        )
        self.scope_manager.add_symbol(symbol)
        with self.scope_manager.new_scope():
            node.name_and_param.accept(self)
            self.add_self_type()
            for param in node.name_and_param.parameters:
                param.accept(self)
                self.add_type_param(param.name.string, parameters_lookup.get(param.name.string))
            utils.visit_all(node.fields, self)


    def visit_type_annotation(self, node: 'TypeAnnotation'):
        self.bind_scope(node)
        utils.visit_all(node.parameters, self)

    def visit_type_instance(self, node: 'TypeInstance'):
        self.bind_scope(node)
        utils.visit_all(node.parameters, self)

    def visit_type_var(self, node: 'TypeVarNode'):
        self.bind_scope(node)
        utils.visit_all(node.constraints, self)

    def visit_trait_function(self, node: 'TraitFunctionNode'):
        self.bind_scope(node)
        utils.visit_all(node.args, self)
        node.return_type.accept(self)

    def visit_trait_def(self, node: 'TraitDefNode'):
        self.bind_scope(node)
        parameters = [utils.get_type_ref_from_type_var(param) for param in node.name_and_param.parameters]
        parameters_lookup = to_lookup(parameters, get_type_name)
        symbol = TraitSymbol(
            name=node.name_and_param.name,
            define=TraitTypeRef(node.name_and_param.name, parameters=parameters),
        )
        self.scope_manager.add_trait(symbol)
        with self.scope_manager.new_scope():
            self.add_self_type()
            for param in node.name_and_param.parameters:
                self.add_type_param(param.name.string, parameters_lookup.get(param.name.string))
                param.accept(self)
            for param in node.functions:
                func = utils.get_function_ref(param, parameters_lookup)
                # func.association_trait = symbol.define
                symbol.define.functions[func.name] = func
            utils.visit_all(node.functions, self)


    def visit_trait_impl(self, node: 'TraitImplNode'):
        self.bind_scope(node)

        """
        trait A<T>{
            def func(a: T) -> T
        }
        
        impl <T: Into> A<T> for B{
            def func(a: T) -> T
        }
        
        todo: need to check: func signature should be same like below
             # def func(a: T, b: string) -> T; error 
             # def func(a: String) -> T; error
             # def func(a: T) ->  String; error
        """

        with self.scope_manager.new_scope():
            node.trait.accept(self)
            node.target_type.accept(self)



            params = [utils.get_type_ref_from_type_var(x) for x in node.type_parameters]
            params_lookup = to_lookup(params, lambda p: p.name)

            trait_ref = utils.get_trait_ref(node.trait, params_lookup)
            target_type = utils.get_type_ref(node.target_type, params_lookup)

            utils.visit_all(node.type_parameters, self)
            utils.visit_all(node.functions, self)

            self.scope_manager.add_symbol(VarSymbol("self", target_type))

            # add type param T to scope to let function can refer
            [self.add_type_param(x.name, x) for x in params]

            node.impl_detail = TraitImpl(
                trait=trait_ref,
                target_type=target_type,
                type_parameters=params,
            )

        self.trait_impls.add_impl(node.impl_detail)



    def visit_var_def(self, node: 'VarDefNode'):
        self.bind_scope(node)
        node.var_node.accept(self)
        node.var_type and node.var_type.accept(self)
        node.init_expr and node.init_expr.accept(self)



    def visit_var(self, node: 'VarNode'):
        self.bind_scope(node)


    def visit_function_def(self, node: 'FunctionDefNode'):
        self.bind_scope(node)
        parameters_lookup = {}
        if not node.trait_node:
            parameters = [utils.get_type_ref_from_type_var(param) for param in node.type_parameters]
            parameters_lookup = to_lookup(parameters, lambda p: p.name)
            symbol =  FunctionSymbol(
                    node.name.string,
                    utils.get_function_ref(node, parameters_lookup)
                )
            symbol.type_ref.association_ast = node
            self.scope_manager.add_symbol(symbol)
        with self.scope_manager.new_scope():
            self.bind_scope(node.body)
            for param in node.type_parameters:
                param.accept(self)
                self.add_type_param(param.name.string, parameters_lookup.get(param.name.string))
            utils.visit_all(node.args, self)
            node.return_type.accept(self)
            utils.visit_all(node.body.stmts, self)

    def visit_block(self, node: 'BlockNode'):
        self.bind_scope(node)

    def visit_return(self, node: 'ReturnNode'):
        self.bind_scope(node)
        return node.expr.accept(self)


    def visit_type_constraint(self, node: TypeConstraint):
        self.bind_scope(node)
        utils.visit_all(node.parameters, self)

    def visit_function_call(self, node: 'FunctionCallNode'):
        self.bind_scope(node)
        node.call_source.accept(self)
        utils.visit_all(node.args, self)

    def visit_struct_init(self, node: 'StructInitNode'):
        self.bind_scope(node)
        with self.scope_manager.new_scope():
            for id_node, expr in node.body:
                expr.accept(self)
        return TypeRef(node.type_name.name)

    def visit_assign(self, node: 'AssignNode'):
        node.var.accept(self)
        node.assign_expr.accept(self)

    def visit_attribute(self, node: 'AttributeNode'):
        self.bind_scope(node)
        node.data.accept(self)
        node.attr.accept(self)


class TypeDetailVisitor(Visitor):
    def __init__(self, scope_manager: ScopeManager, trait_impls: TraitImpls):
        self.scope_manager = scope_manager
        self.trait_impls = trait_impls
        self.expect_types: List[TypeRef] = []
        self.vtable: Dict[str, FunctionDefNode] = {}


    def visit_type_instance(self, node: 'TypeInstance'):
        symbol = node.scope.lookup_type(node.name)
        if symbol is None:
            raise Exception(f"type {node.name} is not defined")
        if isinstance(symbol.define, PrimitiveType):
            return TypeRef(node.name)
        elif isinstance(symbol.define, TypeVar):
            if node.parameters:
                raise Exception(f"type var don't support parameters")
            return symbol.define
        else:
            expect_params_size = len(symbol.define.parameters)
            params_size = len(node.parameters)
            if expect_params_size != params_size:
                raise ValueError(f"type '{node.name}' expected {expect_params_size} params, got {params_size}")
            return TypeRef(node.name, parameters=[x.accept(self) for x in node.parameters])


    def visit_type_annotation(self, node: 'TypeAnnotation'):
        utils.visit_all(node.parameters, self)
        symbol = node.scope.lookup_type(node.name)
        assert symbol is not None


    def visit_struct_def(self, node: 'StructDefNode'):
        symbol = self.scope_manager.lookup_type(node.name_and_param.name)
        assert symbol is not None
        node.name_and_param.accept(self)
        utils.visit_all(node.fields, self)
        for _, type_instance in symbol.define.fields.items():
            if not TypeVar.is_a_var(type_instance) and type_instance.parameters:
                type_def = self.scope_manager.lookup_type(type_instance.name)
                for param_instance, param_def in zip(type_instance.parameters, type_def.parameters):
                    for constraint in param_def.constraints:
                        type_constraint_validate(param_instance, constraint, self.trait_impls)

    def visit_type(self, node: 'StructNode'):
        res = node.scope.lookup_type(node.name)
        if not res:
            raise TypeError(f"Type {node.start_pos} {node.name} is not defined")
        return res.define

    def visit_var_def(self, node: 'VarDefNode'):
        has_var_type = False
        decl_type = None
        infer_type = None
        if node.var_type:
            decl_type = node.var_type.accept(self)
            self.expect_types.append(decl_type)
            has_var_type = True
        if node.init_expr:
            infer_type = node.init_expr.accept(self)
            has_var_type and self.expect_types.pop()

        assert infer_type is not None

        if decl_type and decl_type != infer_type:
            raise ValueError(f"expected type {decl_type} but got {infer_type}")

        stype = infer_type

        node.type_ref = stype

        assert stype is not None
        if isinstance(stype, TypeRef):
            node.scope.add_var(VarSymbol(node.var_node.string, stype))
        elif isinstance(stype, FunctionTypeRef):
            node.scope.add_var(FunctionSymbol(node.var_node.string, stype))
        elif isinstance(stype, TypeVar):
            node.scope.add_var(VarSymbol(node.var_node.string, stype))
        return stype

    def visit_function_type(self, node: 'FunctionTypeNode'):
        parameters = [arg.accept(self) for arg in node.args]
        return FunctionTypeRef(name=None, parameters=parameters, return_type=node.return_type.accept(self))

    def visit_function_def(self, node: 'FunctionDefNode'):
        symbol = self.scope_manager.lookup_var(node.name.string)
        type_ref = symbol.type_ref
        parameters_lookup = to_lookup(type_ref.type_parameters, lambda p: p.name)
        utils.visit_all(node.type_parameters, self)
        for arg in node.args:
            node.body.scope.add_var(VarSymbol(arg.var_node.string, utils.get_type_ref(arg.var_type, parameters_lookup)))
        node.return_type and node.return_type.accept(self)
        for stmt in node.body.stmts:
            if isinstance(stmt, ReturnNode):
                return_type = stmt.accept(self)
                stmt.expr_type = return_type
                stmt.expect_type = type_ref.return_type
                utils.validate_return_type(return_type, symbol.type_ref.return_type, self.trait_impls)
            else:
                stmt.accept(self)

    def visit_trait_function(self, node: 'TraitFunctionNode') -> FunctionTypeRef:
        utils.visit_all(node.args, self)
        node.return_type.accept(self)

    def visit_return(self, node: 'ReturnNode'):
        return node.expr.accept(self)


    def visit_trait_def(self, node: 'TraitDefNode'):
        symbol = self.scope_manager.lookup_traits(node.name_and_param.name)
        assert symbol is not None


    def visit_type_constraint(self, node: TypeConstraint):
        trait = node.scope.lookup_traits(node.trait.name)
        if not trait:
            raise TypeError("trait {} is not defined".format(node.trait.name))
        if len(node.parameters) != len(trait.define.parameters):
            raise TypeError(f"expect {len(trait.define.parameters)} type args but got {len(node.parameters)} for trait {node.trait.name} ")
        utils.visit_all(node.parameters, self)

    def visit_var(self, node: 'VarNode'):
        var = node.scope.lookup_var(node.identifier.string)
        if not var:
            raise ValueError(f"var {node.identifier.string} is not defined")
        return var.type_ref

    def visit_function_call(self, node: 'FunctionCallNode'):
        define = node.call_source.accept(self)
        if isinstance(define, FunctionTypeRef):
            type_binder = TypeBinder(self.trait_impls)
            if len(define.args) != len(node.args):
                raise TypeError(f"function expect {len(define.args)} args but got {len(node.args)}")
            for arg, defined_type in zip(node.args, define.args):
                expr_type = arg.accept(self)
                type_binder.resolve(defined_type, expr_type)

            impl = define.association_impl
            trait_ref = TraitRef(impl.trait.name, [type_binder.bind(x) for x in impl.trait.parameters]) if impl else None
            ref = type_binder.bind(define.return_type)

            # if ref.name == "ANON_TYPE_VAR":
            #     for statement in define.association_ast.body.stmts:
            #         if isinstance(statement, ReturnNode):
            #             return_type = statement.accept(self)
            #             for impl in self.trait_impls.get_impl_by_type(return_type):
            #                 if hit := impl.functions.get(define.association_ast.name):
            #                     ref = impl

            node.type_binds = type_binder.get_binds()
            node.define_ast = define.association_ast
            node.dyn_trait = define.association_trait
            node.call_ref = define
            if trait_ref:
                node.trait_impl = TraitImpl(
                    trait=trait_ref,
                    target_type=impl.target_type,
                    type_parameters=impl.type_parameters,
                    functions=impl.functions
                )
            return utils.de_ref(ref, node.scope)
        elif isinstance(define, MultiResolvedFunction):
            """
                如果一个 struct 实现了多个 trait，比如:
                impl Into<String> for Type1
                impl Into<Int> for Type1
                那边当遍历到 type1.into() 的时候并不知道要调用实现的哪个 trait 的方法，
                因此必须当有类型上下文，比如:
                let x: String = type1.into(); 时才能决定调用的是 Into<String> 的 into 方法
            """

            filter_by_args: List[(FunctionTypeRef, TypeBinder)] = []
            for define in define.functions:
                type_binder = TypeBinder(self.trait_impls)
                if len(define.args) != len(node.args):
                    raise TypeError(f"function expect {len(define.args)} args but got {len(node.args)}")
                arg_types = []
                for arg, defined_type in zip(node.args, define.args):
                    expr_type = arg.accept(self)
                    arg_types.append(expr_type)
                    if defined_type.is_var:
                        type_binder.resolve(defined_type, expr_type)
                func_def = type_binder.bind(define)
                func_def.association_impl = define.association_impl
                func_def.association_ast = define.association_ast
                if define.args == arg_types:
                    filter_by_args.append((func_def, type_binder))

            final_res = None
            final_builder = None
            if len(filter_by_args) > 1:
                for func_def, type_binder in filter_by_args:
                    if not self.expect_types:
                        raise ValueError("can not resolve multiple defined function")
                    expect_type = self.expect_types[-1]
                    if func_def.return_type == expect_type:
                        final_res = func_def
                        final_builder = type_binder
            else:
                final_res, final_builder = filter_by_args[0]

            impl = final_res.association_impl
            trait_ref = TraitRef(impl.trait.name,
                                 [final_builder.bind(x) for x in impl.trait.parameters]) if impl else None
            node.define_ast = final_res.association_ast
            node.dyn_trait = define.association_trait
            node.call_ref = define
            if trait_ref:
                node.trait_impl = TraitImpl(
                    trait=trait_ref,
                    target_type=impl.target_type,
                    type_parameters=impl.type_parameters,
                    functions=impl.functions
                )

            return utils.de_ref(final_res.return_type, node.scope)
        else:
            raise TypeError(f"{define.name} is not callable")


    def visit_type_var(self, node: 'TypeVarNode'):
        utils.visit_all(node.constraints, self)
        return node.scope.lookup_type(node.name.string)

    def visit_trait_impl(self, node: 'TraitImplNode'):
        symbol = node.scope.lookup_traits(node.trait_name)
        if not symbol:
            raise ValueError(f"trait {node.trait_name} is not defined")
        utils.visit_all(node.type_parameters, self)
        node.trait.accept(self)
        node.target_type.accept(self)

        trait_impl = node.impl_detail


        # 计算类型映射
        # 定义: trait Trait<U>
        # 实现: impl <T> Trait<T> for Target<T>
        # 将 U 映射为 T
        type_binds = {}
        for defined_param, real_param in zip(symbol.define.parameters, trait_impl.trait.parameters):
            type_binds[defined_param] = real_param

        """
            1. 替换 trait 定义的类型为真实类型
            2. 替换定义中的 function 为真实类型
            3. 与实现中的类型做比较是否一致
        """
        type_lookup = utils.to_lookup(trait_impl.trait.parameters, lambda p: p.name)
        for function in node.functions:
            # 计算 function 的实现类型
            impl_function_ref = utils.get_function_ref(function, type_lookup)
            impl_function_ref.association_ast = function
            impl_function_ref.association_impl = trait_impl

            trait_impl.functions[impl_function_ref.name] = impl_function_ref

            # 计算 trait 类型映射之后的真实类型
            trait_function_def = utils.bind_type(symbol.define.functions[impl_function_ref.name], type_binds)


            if len(impl_function_ref.args) != len(trait_function_def.args):
                raise TypeError(f"expect {len(impl_function_ref.args)} args but got {len(trait_function_def.args)}")
            for r1, r2 in zip(impl_function_ref.args, trait_function_def.args):
                if not utils.equal_without_constraint(r1, r2):
                    raise Exception(
                        f"function '{function.name.string}' not match sign define in trait {node.trait_name}")
            if not utils.equal_without_constraint(impl_function_ref.return_type, trait_function_def.return_type):
                raise Exception(
                    f"function '{function.name.string}' not match sign define in trait {node.trait_name}, expect: {trait_function_def.return_type}, but got {impl_function_ref.return_type}")
            for arg, arg_type in zip(function.args, impl_function_ref.args):
                function.body.scope.add_var(VarSymbol(arg.var_node.string, arg_type))
            for stmt in function.body.stmts:
                if isinstance(stmt, ReturnNode):
                    return_type = stmt.accept(self)
                    utils.validate_return_type(return_type, trait_function_def.return_type, self.trait_impls)
                else:
                    stmt.accept(self)


    def visit_lit(self, node: 'LiteralNode'):
        return TypeRef(node.literal_type)

    def visit_struct_init(self, node: 'StructInitNode') -> TypeRef:
        symbol = self.scope_manager.lookup_type(node.type_name.name)
        define = symbol.define
        type_binder = TypeBinder(self.trait_impls)
        for var, expr in node.body:
            field_name = var.string
            if field_name not in define.fields:
                raise TypeError(f"Field {field_name} is not defined in type {node.type_name.name}")
            expr_type = expr.accept(self)
            defined_type = define.fields[field_name]
            type_binder.resolve(defined_type, expr_type)
        type_ref = type_binder.bind(TypeRef(node.type_name.name, symbol.parameters))
        res = utils.de_ref(type_ref, node.scope.child)
        node.type_ref = res
        return res

    def visit_attribute(self, node: 'AttributeNode'):
        type_ref: TypeRef|TypeVar = node.data.accept(self)
        # should be a trait here, lookup function with name attribute
        if type_ref.is_var:
            if type_ref.constraints:
                for trait in type_ref.constraints:
                    trait_symbol = node.scope.lookup_traits(trait.name)
                    binds = {}
                    for const_trait, defined_type in zip(trait.parameters, trait_symbol.define.parameters):
                        binds[defined_type] = const_trait
                    if func := trait_symbol.define.functions.get(node.attr.string):
                        return FunctionTypeRef(
                            name=func.name,
                            args=[utils.bind_type(x, binds) for x in func.args],
                            return_type=utils.bind_type(func.return_type, binds),
                            association_trait=trait,
                            call_source_type=type_ref
                        )
                raise TypeError(f"function {node.attr.string} is not defined for constraint: {type_ref.constraints}")
            else:
                #print(type_ref)
                raise TypeError(f"attribute not available for no constraint generic type")
        # 如果 struct 中没找到对应的 attr，就尝试去 trait 中寻找方法
        if type_ref.struct_ref and node.attr.string in type_ref.struct_ref.fields:
            return type_ref.struct_ref.fields[node.attr.string]
        else:
            impl_traits = self.trait_impls.get_impl_by_type(type_ref)
            function_hits = []
            for impl in impl_traits:
                if hit := impl.functions.get(node.attr.string):
                    hit.call_source_type = type_ref
                    function_hits.append(hit)
            if function_hits:
                return MultiResolvedFunction(function_hits) if len(function_hits) > 1 else function_hits[0]
            raise TypeError(f"Attribute {node.attr.string} is not defined in type {type_ref}")
