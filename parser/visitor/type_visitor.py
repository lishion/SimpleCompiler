from _ast import FunctionDef
from array import ArrayType
from typing import Dict
from parser.symbol_type import StructTypeRef, TraitTypeRef, FunctionTypeRef, TypeRef, TraitImpl, TraitRef, \
    PrimitiveType, \
    StructType, MultiResolvedFunction, TypeVar, ResolvedFunctionRef, ResolvedFunction
from parser.node import *
from parser.scope import ScopeManager, TraitImpls
from parser.symbol import TypeSymbol, TraitSymbol, GenericParamSymbol, FunctionSymbol, VarSymbol
from parser.visitor import utils, type_binder
from parser.visitor.type_binder import TypeBinder
from parser.visitor.utils import to_lookup, get_type_name
from copy import copy, deepcopy
from itertools import chain
from dataclasses import dataclass, field
from utils.logger import LOGGER

class TypeDefVisitor(Visitor):

    def __init__(self, scope_manager: ScopeManager, trait_impls: TraitImpls):
        self.scope_manager = scope_manager
        self.trait_impls = trait_impls

    def add_self_type(self):
        self.scope_manager.add_symbol(TypeSymbol('Self', define=None, parameters={}))

    def add_type_param(self, name: str, type_var: TypeVar):
        self.scope_manager.add_symbol(GenericParamSymbol(name, type_var))

    def add_type_params(self, type_vars: List[TypeVar]):
        for type_var in type_vars:
            self.add_type_param(type_var.name, type_var)

    def bind_scope(self, ast: 'ASTNode'):
        ast.scope = self.scope_manager.current_scope

    def visit_struct_def(self, node: 'StructDefNode', context=None):
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
            self.add_self_type()
            for param in node.name_and_param.parameters:
                self.add_type_param(param.name.string, parameters_lookup.get(param.name.string))
                param.accept(self)
            node.name_and_param.accept(self)
            utils.visit_all(node.fields, self)


    def visit_type_annotation(self, node: 'TypeAnnotation', context=None):
        self.bind_scope(node)
        utils.visit_all(node.parameters, self)

    def visit_type_instance(self, node: 'TypeInstance', context=None):
        self.bind_scope(node)
        type_var = self.scope_manager.lookup_type(node.name)
        if not type_var:
            raise ValueError(f"type {node.name} is not defined")
        if isinstance(type_var, GenericParamSymbol):
            node.type_ref = type_var.define
        else:
            utils.visit_all(node.parameters, self)

    def visit_type_var(self, node: 'TypeVarNode', context=None):
        self.bind_scope(node)
        utils.visit_all(node.constraints, self)
        type_var: GenericParamSymbol = self.scope_manager.lookup_type(node.name.string)
        if not type_var:
            raise ValueError(f"type var {node.name.string} is not defined")
        node.type_ref = type_var.define



    def visit_trait_function(self, node: 'TraitFunctionNode', context=None):
        self.bind_scope(node)
        utils.visit_all(node.args, self)
        node.return_type.accept(self)

    def visit_trait_def(self, node: 'TraitDefNode', context=None):
        self.bind_scope(node)
        self_type = TypeVar.create("Self")
        parameters = [utils.get_type_ref_from_type_var(param) for param in node.name_and_param.parameters]

        parameters_lookup = to_lookup(parameters, get_type_name)
        symbol = TraitSymbol(
            name=node.name_and_param.name,
            define=TraitTypeRef(node.name_and_param.name, parameters=parameters),
            self_type=self_type
        )
        self.scope_manager.add_trait(symbol)
        with self.scope_manager.new_scope():
            parameters_lookup['Self'] = self_type
            self.add_type_params([self_type])
            for param in node.name_and_param.parameters:
                self.add_type_param(param.name.string, parameters_lookup.get(param.name.string))
                param.accept(self)
            for param in node.functions:
                func = utils.get_function_ref(param, parameters_lookup)
                symbol.define.functions[func.name] = func
            utils.visit_all(node.functions, self)


    def visit_trait_impl(self, node: 'TraitImplNode', context=None):
        #self.bind_scope(node)

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

        with self.scope_manager.new_scope() as scope:

            self.bind_scope(node)

            params = [utils.get_type_ref_from_type_var(x) for x in node.type_parameters]
            params_lookup = to_lookup(params, lambda p: p.name)
            [self.add_type_param(x.name, x) for x in params]

            node.trait.accept(self)
            node.target_type.accept(self)

            trait_ref = utils.get_trait_ref(node.trait, params_lookup)
            target_type = utils.get_type_ref(node.target_type, params_lookup)

            utils.visit_all(node.type_parameters, self)
            self.scope_manager.add_symbol(VarSymbol("self", target_type))
            self.scope_manager.add_symbol(GenericParamSymbol("Self", TypeVar.create("Self")))
            utils.visit_all(node.functions, self)

            # add type param T to scope to let function can refer

            node.impl_detail = TraitImpl(
                trait=trait_ref,
                target_type=target_type,
                type_parameters=params,
            )

        self.trait_impls.add_impl(node.impl_detail)



    def visit_var_def(self, node: 'VarDefNode', context=None):
        self.bind_scope(node)
        node.var_node.accept(self, context)
        node.var_type and node.var_type.accept(self, context)
        node.init_expr and node.init_expr.accept(self, context)



    def visit_var(self, node: 'VarNode', context=None):
        self.bind_scope(node)


    def visit_function_def(self, node: 'FunctionDefNode', context=None):
        self.bind_scope(node)
        parameters_lookup = {}
        if not node.trait_node:
            parameters = [utils.get_type_ref_from_type_var(param) for param in node.type_parameters]
            parameters_lookup = to_lookup(parameters, lambda p: p.name)
            symbol = FunctionSymbol(
                    node.name.string,
                    utils.get_function_ref(node, parameters_lookup)
            )
            symbol.type_ref.association_ast = node
            self.scope_manager.add_symbol(symbol)
        with self.scope_manager.new_scope():
            self.bind_scope(node.body)
            for param in node.type_parameters:
                self.add_type_param(param.name.string, parameters_lookup.get(param.name.string))
                param.accept(self)
            utils.visit_all(node.args, self)
            node.return_type.accept(self)
            utils.visit_all(node.body.stmts, self)
            for stmt in node.body.stmts:
                if isinstance(stmt, VarDefNode):
                    stmt.accept(self)

    def visit_block(self, node: 'BlockNode', context=None):
        self.bind_scope(node)

    def visit_return(self, node: 'ReturnNode', context=None):
        self.bind_scope(node)
        return node.expr.accept(self, context)


    def visit_type_constraint(self, node: TypeConstraint, context=None):
        self.bind_scope(node)
        utils.visit_all(node.parameters, self)

    def visit_function_call(self, node: 'FunctionCallNode', context=None):
        self.bind_scope(node)
        node.call_source.accept(self)
        utils.visit_all(node.args, self)

    def visit_struct_init(self, node: 'StructInitNode', context=None):
        self.bind_scope(node)
        with self.scope_manager.new_scope():
            for id_node, expr in node.body:
                expr.accept(self, context)
        return TypeRef(node.type_name.name)

    def visit_assign(self, node: 'AssignNode', context=None):
        node.var.accept(self)
        node.assign_expr.accept(self)

    def visit_attribute(self, node: 'AttributeNode', context=None):
        self.bind_scope(node)
        node.data.accept(self, context)
        node.attr.accept(self, context)

    def visit_bin_op(self, node: 'BinaryOpNode', parse_context: None=None):
        self.bind_scope(node)
        node.left.accept(self, parse_context)
        node.right.accept(self, parse_context)

@dataclass
class TypeContext:

    # 保存函数调用时预期的类型，例如
    # let a: Int = x.into(); 此时期望 x.into() 返回 Int 类型的值
    func_expect_return_type: TypeRef = None

    type_binds: Dict['TypeVar', TypeRef] = field(default_factory=dict)

    # 当进行泛型单态化时需要对 Scope 进行拷贝
    scope_copy: 'Scope' = None


class TypeDetailVisitor(Visitor):
    def __init__(self, scope_manager: ScopeManager, trait_impls: TraitImpls):
        self.scope_manager = scope_manager
        self.trait_impls = trait_impls
        self.expect_types: List[TypeRef] = []
        self.vtable: Dict[str, FunctionDefNode] = {}


    def visit_type_instance(self, node: 'TypeInstance', context=None) -> TypeRef|TypeVar:
        symbol = node.scope.lookup_type(node.name)
        if symbol is None:
            raise Exception(f"type {node.name} is not defined")
        if isinstance(symbol.define, PrimitiveType):
            return TypeRef(node.name)
        elif isinstance(symbol.define, TypeVar):
            if node.parameters:
                raise Exception(f"type var don't support parameters")
            return symbol.define
        elif isinstance(symbol.define, TypeRef) and symbol.define.is_primitive_type:
            return symbol.define
        else:
            expect_params_size = len(symbol.define.parameters)
            params_size = len(node.parameters)
            if expect_params_size != params_size:
                raise ValueError(f"type '{node.name}' expected {expect_params_size} params, got {params_size}")
            return TypeRef(node.name, parameters=[x.accept(self) for x in node.parameters])


    def visit_type_annotation(self, node: 'TypeAnnotation', context=None):
        utils.visit_all(node.parameters, self)
        symbol = node.scope.lookup_type(node.name)
        assert symbol is not None


    def visit_struct_def(self, node: 'StructDefNode', context=None):
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

    def visit_type(self, node: 'StructNode', context=None):
        res = node.scope.lookup_type(node.name)
        if not res:
            raise TypeError(f"Type {node.start_pos} {node.name} is not defined")
        return res.define

    def visit_var_def(self, node: 'VarDefNode', context: TypeContext=None):
        decl_type = None
        infer_type = None
        if node.var_type:
            decl_type = node.var_type.accept(self)
            self.expect_types.append(decl_type)
        if node.init_expr:
            infer_type = node.init_expr.accept(self, TypeContext(func_expect_return_type=decl_type))

        assert infer_type is not None

        if decl_type and not self.trait_impls.is_type_match(infer_type, decl_type):
            raise ValueError(f"expected type {decl_type} but got {infer_type}")

        stype = infer_type

        node.type_ref = stype

        assert stype is not None
        # 如果有 context，则说明是对泛型函数进行编译，此时不需要再定义变量，否则会重复定义
        if not context:
            if isinstance(stype, TypeRef):
                node.scope.add_var(VarSymbol(node.var_node.string, stype))
            elif isinstance(stype, FunctionTypeRef):
                node.scope.add_var(FunctionSymbol(node.var_node.string, stype))
            elif isinstance(stype, TypeVar):
                node.scope.add_var(VarSymbol(node.var_node.string, stype))
        return stype

    def visit_function_type(self, node: 'FunctionTypeNode', context=None):
        parameters = [arg.accept(self) for arg in node.args]
        return FunctionTypeRef(name=None, parameters=parameters, return_type=node.return_type.accept(self))

    def visit_function_def(self, node: 'FunctionDefNode', context: TypeContext=None):
        if not context:
            # 第一次对没有泛型参数/或者有泛型参数的模板进行编译
            symbol = self.scope_manager.lookup_var(node.name.string)
            type_ref = symbol.type_ref
            parameters_lookup = to_lookup(type_ref.type_parameters, lambda p: p.name)
            utils.visit_all(node.type_parameters, self)
            for arg in node.args:
                node.body.scope.add_var(VarSymbol(arg.var_node.string, utils.get_type_ref(arg.var_type, parameters_lookup)))
            node.return_type and node.return_type.accept(self)
            for stmt in node.body.stmts:
                if isinstance(stmt, ReturnNode):
                    return_type = stmt.accept(self, context)
                    stmt.expr_type = return_type
                    stmt.expect_type = type_ref.return_type
                    if not self.trait_impls.is_type_match(return_type, type_ref.return_type):
                        raise TypeError(f"type {return_type} dot not match type {type_ref.return_type}")
                else:
                    stmt.accept(self, context)
        else:
            #pass
            #symbol = self.scope_manager.lookup_var(node.name.string)
            # type_ref = utils.bind_type(symbol.type_ref, context.type_binds)
            for stmt in node.body.stmts:
                # if isinstance(stmt, FunctionCallNode):
                #     # for arg in stmt.args:
                #     #     if isinstance(arg, FunctionCallNode):
                #     #         arg.accept(self, context)
                #     print(f"visit func {stmt.call_source} by context {context}")
                #     stmt.accept(self, context)
                stmt.accept(self, context)


    def visit_trait_function(self, node: 'TraitFunctionNode', context=None) -> FunctionTypeRef:
        utils.visit_all(node.args, self)
        node.return_type.accept(self)

    def visit_return(self, node: 'ReturnNode', context=None):
        return node.expr.accept(self, context)


    def visit_trait_def(self, node: 'TraitDefNode', context=None):
        symbol = self.scope_manager.lookup_traits(node.name_and_param.name)
        assert symbol is not None


    def visit_type_constraint(self, node: TypeConstraint, context=None):
        trait = node.scope.lookup_traits(node.trait.name)
        if not trait:
            raise TypeError("trait {} is not defined".format(node.trait.name))
        if len(node.parameters) != len(trait.define.parameters):
            raise TypeError(f"expect {len(trait.define.parameters)} type args but got {len(node.parameters)} for trait {node.trait.name} ")
        utils.visit_all(node.parameters, self)

    def visit_var(self, node: 'VarNode', context=None):
        var = node.scope.lookup_var(node.identifier.string)
        if not var:
            raise ValueError(f"var {node.identifier.string} is not defined")
        return var.type_ref

    def visit_function_call(self, node: 'FunctionCallNode', type_context: TypeContext=None):
        """
            对于带泛型函数的分派有以下几种情况:
                对于普通函数: def id<T>(t: T) -> T

                    单态化，也就是针对不同类型的调用生成不同的函数:
                        当遇到 id(Int) 时会编译出一个 id__Int 函数，例如 id(1)。调用时为 id__Int(1)
                        当遇到 id(String) 时会编译出一个 id__String 函数，同样调用时也是 id__String("1")
                    如果参数中含有 dyn object，例如:
                        let x: dyn Trait1 = 1
                        id(x)
                    这种时候不会进行单态化，函数名为定义时的函数名。
                对于 trait 函数，例如 trait Debug { def show() -> String }, t.show()
                    单态化，如果 t 的类型是一个确切的类型，例如 Int, 那么 1.into 会被编译为 Debug_for_Int___into，调用时为 Debug_for_Int___into(1)
                    当然 t 也可能是 dyn object，例如  let x: dyn Debug = 1，那么不会进行单态化，调用时为 obj.get_attr(into).get('Debug') // 先获取 dyn obj 的 attr 属性，然后调用 .get('Debug') 获取对应的 vtable 的函数

        :param node:
        :param type_context:
        :return:
        """
        type_context = type_context or TypeContext()
        function_define = node.call_source.accept(self, type_context)
        function_define_source = function_define
        source_ref = getattr(function_define_source, 'source_ref', None)
        source_ref = source_ref and utils.bind_type(source_ref, type_context.type_binds)

        node.dyn_dispatch = TypeVar.is_a_var(source_ref)

        #node.scope.lookup_type("Self")



        if isinstance(function_define, FunctionTypeRef):
            function_define = function_define.to_resolved()
        elif isinstance(function_define, ResolvedFunction):
            function_define = function_define.function

        if isinstance(function_define, ResolvedFunctionRef):
            LOGGER.info("function '%s' use dyn dispatch: %s", function_define.name, node.dyn_dispatch)
            if len(function_define.args) != len(node.args):
                raise TypeError(f"function {function_define.name} expect {len(function_define.args)} args but got {len(node.args)}")
            type_binder = TypeBinder(self.trait_impls)
            for arg, defined_type in zip(node.args, function_define.args):
                # 根据入参的类型，对函数的类型变量进行绑定
                # 这里需要将已经绑定的变量添加到 all_binds 中，以便后续的参数可以使用
                # 比如 def foo<T>(t1: T, t2: T)，如果有 foo(1, xxx)，当解析了第一个参数的类型为 Int，那么第二个参数的类型也需要被绑定为 Int
                all_binds = type_context.type_binds | type_binder.get_binds()
                bind_type = utils.bind_type(defined_type, all_binds)
                expr_type = arg.accept(self, TypeContext(func_expect_return_type=bind_type, type_binds=all_binds))
                type_binder.resolve(defined_type, expr_type)
            bind_function = type_binder.bind(function_define)

            node.type_binds = type_binder.get_binds()
            node.define_ast = deepcopy(function_define.association_ast)
            node.call_ref = bind_function

            # 如果不是动态分派则进行单态化
            if not node.dyn_dispatch and node.define_ast:
                scope = node.define_ast.scope.child
                new_symbols = {}
                for var_name, var_symbol in scope.symbols.items():
                    new_symbols[var_name] = VarSymbol(var_name, utils.bind_type(var_symbol.type_ref, node.type_binds))
                scope.symbols = new_symbols
                node.define_ast and node.define_ast.accept(self, TypeContext(type_binds=type_binder.get_binds() | type_context.type_binds | function_define.binds))
            return utils.de_ref(bind_function.return_type, node.scope)
        elif isinstance(function_define, MultiResolvedFunction):
            """
                # 如果一个 struct 实现了多个 trait，比如:
                # impl Into<String> for Type1
                # impl Into<Int> for Type1
                # 那边当遍历到 type1.into() 的时候并不知道要调用实现的哪个 trait 的方法，
                # 因此必须当有类型上下文，比如:
                # let x: String = type1.into(); 时才能决定调用的是 Into<String> 的 into 方法
                当解析到多个函数时，需要根据入参类型和返回值类型来进行过滤，获取类型匹配的函数
                并且，如果最终仍有多个函数，那么:
                1. 如果多个函数是是同一个 trait 的实现，且此时是动态分派的场景，则可以不报错，比如
                   impl Into<String> for Type1
                   impl Into<String> for Type2
                   由于 call source 定义可能是 dyn Into<String>，因此可以调用 Type1.into() 或 Type2.into() 都没有问题
                2. 其余情况都应该报错
            """
            filter_by_args: List[(FunctionTypeRef, TypeBinder)] = []
            for func in function_define.functions:
                type_binder = TypeBinder(self.trait_impls)
                if len(func.args) != len(node.args):
                    raise TypeError(f"function expect {len(func.args)} args but got {len(node.args)}")
                arg_type_mismatch = False
                # 当函数有多个匹配时，需要从入参类型，和返回值类型来进行过滤，获取类型匹配的函数
                for arg, defined_type in zip(node.args, func.args):
                    # 根据入参的类型，对函数的类型变量进行绑定
                    # 这里需要将已经绑定的变量添加到 all_binds 中，以便后续的参数可以使用
                    # 比如 def foo<T>(t1: T, t2: T)，如果有 foo(1, xxx)，当解析了第一个参数的类型为 Int，那么第二个参数的类型也需要被绑定为 Int
                    all_binds = type_context.type_binds | type_binder.get_binds()
                    bind_type = utils.bind_type(defined_type, all_binds)
                    expr_type = arg.accept(self, TypeContext(func_expect_return_type=bind_type, type_binds=all_binds))
                    try:
                        type_binder.resolve(defined_type, expr_type)
                    except TypeError as e:
                        # 如果无法绑定，则说明类型不一致，该函数不是当前需要的函数
                        arg_type_mismatch = True
                        break
                if arg_type_mismatch:
                    continue
                func_def = type_binder.bind(func)
                if type_context and type_context.func_expect_return_type and not TypeVar.is_a_var(type_context.func_expect_return_type):
                    if self.trait_impls.is_type_match(type_context.func_expect_return_type, func_def.return_type):
                        filter_by_args.append((func_def, type_binder))
                else:
                    filter_by_args.append((func_def, type_binder))
            if not filter_by_args:
                raise TypeError(f"function '{function_define.functions[0].name}' not found")

            if len(filter_by_args) > 1:
                traits = set([str(x[0].association_trait) for x in filter_by_args])
                LOGGER.info("all traits %s match args type", list(traits))
                # 如果有多个函数匹配，但都属于同一个 trait 的实现，并且是动态分派的场景，则可以不报错
                if node.dyn_dispatch and len(traits) <= 1:
                    # 如果是同一个 trait，那么方法签名是一致的，选第一个即可
                    final_res, final_builder = filter_by_args[0]
                    node.type_binds = final_builder.get_binds()
                    node.call_ref = final_builder.bind(final_res)
                    return utils.de_ref(node.call_ref.return_type, node.scope)
                else:
                    raise TypeError(f"multiple func match, '{function_define.functions[0].name}' in {traits}")
            else:
                final_res, final_builder = filter_by_args[0]
                node.type_binds = final_builder.get_binds()
                node.define_ast = final_res.association_ast
                node.call_ref = final_builder.bind(final_res)
                return utils.de_ref(node.call_ref.return_type, node.scope)
        else:
            raise TypeError(f"{function_define.name} is not callable")


    def visit_type_var(self, node: 'TypeVarNode', context=None):
        utils.visit_all(node.constraints, self)
        return node.scope.lookup_type(node.name.string)

    def visit_trait_impl(self, node: 'TraitImplNode', context=None):
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
        # 替换 Self 为具体的实现类型
        type_binds = {symbol.self_type: trait_impl.target_type}
        for defined_param, real_param in zip(symbol.define.parameters, trait_impl.trait.parameters):
            type_binds[defined_param] = real_param

        """
            1. 替换 trait 定义的类型为真实类型
            2. 替换定义中的 function 为真实类型
            3. 与实现中的类型做比较是否一致
        """

        type_lookup = utils.to_lookup(trait_impl.trait.parameters, lambda p: p.name)

        # 替换 Self 为具体的实现类型
        type_lookup['Self'] = trait_impl.target_type
        impl_self_type = node.scope.lookup_type('Self')
        impl_self_type.define = trait_impl.target_type

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
                        f"function '{function.name.string}' not match sign define in trait {node.trait_name}, expect: {r2}, but got {r1}")
            if not utils.equal_without_constraint(impl_function_ref.return_type, trait_function_def.return_type):
                raise Exception(
                    f"function '{function.name.string}' not match sign define in trait {node.trait_name}, expect: {trait_function_def.return_type}, but got {impl_function_ref.return_type}")
            # 将参数类型绑定为 impl 的具体类型，这里也会将 Self 替换为具体的实现类型
            for arg, arg_type in zip(function.args, impl_function_ref.args):
                function.body.scope.add_var(VarSymbol(arg.var_node.string, arg_type))
            for stmt in function.body.stmts:
                if isinstance(stmt, ReturnNode):
                    return_type = stmt.accept(self)
                    utils.validate_return_type(return_type, trait_function_def.return_type, self.trait_impls)
                else:
                    stmt.accept(self)


    def visit_lit(self, node: 'LiteralNode', context=None):
        return TypeRef(node.literal_type)

    def visit_struct_init(self, node: 'StructInitNode', context=None) -> TypeRef:
        context = context or TypeContext()
        symbol = self.scope_manager.lookup_type(node.type_name.name)
        fields = symbol.define.fields
        type_binder = TypeBinder(self.trait_impls, context.type_binds)
        if context.type_binds:
            pass
        for var, expr in node.body:
            field_name = var.string
            if field_name not in fields:
                raise TypeError(f"Field {field_name} is not defined in type {node.type_name.name}")
            defined_type = fields[field_name]
            # 根据已经绑定的类型来提供类型上下文
            # 例如 def a<T>(t1: T, t2: T)
            # a(1, t1.into())
            # 通过第一个参数 1 可以推断出 T = Int，因此给 t1.into() 提供类型上下文，使其寻找返回 Int 的方法
            bind_type = utils.bind_type(fields[field_name], type_binder.get_binds())
            expr_type = expr.accept(self, TypeContext(func_expect_return_type=bind_type, type_binds=context.type_binds))
            type_binder.resolve(defined_type, expr_type)

        type_ref = type_binder.bind(TypeRef(node.type_name.name, symbol.parameters))
        res = utils.de_ref(type_ref, node.scope.child)
        if context.type_binds:
            LOGGER.info("deref %s to %s when init struct", type_ref, res)
        node.type_ref = res
        return res

    def visit_attribute(self, node: 'AttributeNode', context=None):
        context = context or TypeContext()
        type_ref: TypeRef|TypeVar = node.data.accept(self, context)
        if not TypeVar.is_a_var(type_ref):
            symbol = self.scope_manager.lookup_type(type_ref.name)
            type_ref = utils.bind_type(type_ref, context.type_binds)
            if isinstance(symbol.define, StructTypeRef):
                type_ref = utils.de_ref(type_ref, node.scope)
                LOGGER.info("deref struct type '%s' to %s", type_ref.name, type_ref.struct_ref.fields)
        LOGGER.info("visit attribute '%s', source type: %s", node.attr.string, type_ref)
        function_hits = []
        """
            对于 a.xxx() 来说可能有以下几种情况:
            1. a 是一个具体的类型，比如 Int，那么 xxx 就是 Int 实现的一个方法
            2. a 是一个 dyn Trait，那么 xxx 就是 Trait 约束中定义的一个方法
            
            对于 1 来说，由于一个类型可能有多个实现，并且拥有同名的方法，比如 impl T1 for Int 和 impl T2 for Int 都有同一个方法 xxx，
            那么此时可能会解析出两个函数实现，这种情况下需要返回一个 MultiResolvedFunction
            同样，对于 2 来说，如果 dyn Trait 也可能有多个实现，那么也会返回一个 MultiResolvedFunction
        """
        if type_ref.is_var:
            if type_ref.constraints:
                LOGGER.info("try to find function according to trait %s", type_ref.constraints)
                # 是一个具有约束的类型变量，试图从约束的实现中寻找对应的函数
                for trait in type_ref.constraints:
                    for impl in self.trait_impls.get_impl_by_trait(trait):
                        if func := impl.functions.get(node.attr.string):
                            function_hits.append(func.to_resolved())
                            LOGGER.info("find function '%s' in impl %s for type %s", node.attr.string, trait, func.association_impl.target_type)
            else:
                raise TypeError(f"attribute not available for generic type without constraint")
        # 先试图从 struct 中寻找属性，如果找不到就从 trait 实现中寻找
        elif hasattr(type_ref, 'struct_ref') and type_ref.struct_ref and node.attr.string in type_ref.struct_ref.fields:
            return type_ref.struct_ref.fields[node.attr.string]
        else:
            LOGGER.info("try to find function according to type %s", type_ref)
            impl_traits = self.trait_impls.get_impl_by_type(type_ref)
            for impl in impl_traits:
                if hit := impl.functions.get(node.attr.string):
                    LOGGER.info("impl binds = %s", impl.binds)
                    hit.call_source_type = type_ref
                    resolved_hits = hit.to_resolved()
                    resolved_hits.binds = impl.binds
                    function_hits.append(resolved_hits)
        if function_hits:
            return MultiResolvedFunction(function_hits, type_ref) if len(function_hits) > 1 else ResolvedFunction(function_hits[0], type_ref)

        raise TypeError(f"Attribute {node.attr.string} is not defined in type {type_ref}")

    def visit_bin_op(self, node: 'BinaryOpNode', parse_context: None=None):
        LOGGER.info('context is %s', parse_context)
        left = node.left.accept(self, parse_context)
        right = node.right.accept(self, parse_context)
        if left != right:
            raise TypeError(f"Binary operation {node.op} expect same type for left and right, but got {left} and {right}")
        if TypeVar.is_a_var(left):
            for x in left.constraints:
                if x.name == "Ops":
                    return left
            raise TypeError(f"Type {left} is a type variable without Ops trait constraint")
        elif not self.trait_impls.get_impl(left, TraitRef('Ops')):
            raise TypeError(f"Type '{left}' is not impl trait Ops")
        call_source = AttributeNode(node.left, IdNode("add"))
        call_source.scope = node.scope
        new_node = FunctionCallNode(
            call_source=call_source,
            args=[node.right]
        )
        new_node.scope = node.scope
        node.transformed = new_node
        node.transformed.accept(self, parse_context)
        return left