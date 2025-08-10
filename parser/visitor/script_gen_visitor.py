from typing import Dict
from uuid import uuid4

from parser.scope import TraitImpls
from parser.symbol_type import TraitRef
from runtime.data import MetaManager, CodeFunctionObject, NameFunctionObject
from code_gen.script import PythonCodeGenerator
from parser.node import *
from parser import utils
from dataclasses import dataclass, field
from parser.visitor import utils as type_utils
from utils.logger import LOGGER


@dataclass
class TypeContext:
    trait: TraitRef = None
    type_binds: Dict['TypeVar', TypeRef] = field(default_factory=dict)
    function_name: Optional[str] = None
    return_type: Union[TypeRef, 'TypeVar'] = None

class EvalVisitor(Visitor):
    def __init__(self, meta_manager: MetaManager, code_generator: PythonCodeGenerator, trait_impl: TraitImpls):
        self.meta_manager = meta_manager
        self.code_gen = code_generator
        self.defined_functions = set()
        self.type_contexts: List[TypeContext] = []
        self.function_defs = []
        self.trait_impls = trait_impl

    def visit_bin_op(self, node: 'BinaryOpNode', context=None):
        if node.transformed:
            return node.transformed.accept(self, context)
        left = node.left.accept(self)
        right = node.right.accept(self)
        return f"{left} {node.op} {right}"

    def visit_assign(self, node: 'AssignNode', context=None):
        return f"{node.var.identifier.string}={node.assign_expr.accept(self)}"

    def visit_lit(self, node: 'LiteralNode', context=None):
        match node.literal_type.lower():
            case "float": return f"meta_manager.create_object('Float', {float(node.val)})"
            case "string": return f"meta_manager.create_object('String', '{node.val[1: -1]}')"
            case "int": return f"meta_manager.create_object('Int', {int(node.val)})"
            case "bool": return f"meta_manager.create_object('Bool', {node.val == 'true'})"
            case _: return node.val

    def visit_var(self, node: 'VarNode', context=None):
        return node.identifier.string

    def visit_block(self, node: 'BlockNode', context=None):
        res = "\n".join([utils.indent(stmt.accept(self, context), 1)   for stmt in node.stmts] )
        return res

    def _current_context(self) -> TypeContext:
        return self.type_contexts[-1]

    def visit_function_call(self, node: 'FunctionCallNode', context: TypeContext=None):
        # 如果这个函数是某个 trait 的实现
        trait_name = ""
        context = context or TypeContext()
        function_call_source = node.call_source.accept(self, context)
        current_context = context
        LOGGER.info("start to visit function call %s", function_call_source)
        #LOGGER.info("start to visit function call: %s, %s, %s", node.call_ref.name, node.call_ref.association_trait, node.call_ref.association_type)
        source_function_name = node.call_ref.name
        """
            传递 type resolve, 例如:
            def a<T>(x: T) -> T{
                 return x;
            }

            def b<T>(x: T) -> T{
                 return a(x);
            }

            def c<T>(x: T) -> T{
                return b(x);
            }
            let x = c(1);
            调用 b 时，由于 b 本身也有泛型，因此会得到映射 Tb=Tc，但是在 c 已经求解了 Tc = Int，因此需要将 Tc 替换为 Int，最终将 Tb 也替换为 Int
        """
        bind_binds = type_utils.resolve_type_binds(node.type_binds, current_context.type_binds)

        if node.origin_call_ref:
            for arg_define_type, arg in zip(node.origin_call_ref.args, node.args):
                if TypeVar.is_a_var(arg_define_type) and arg.expr_type.is_primitive_type:
                    self.create_dyn_object(arg.expr_type, arg_define_type.constraints, bind_binds)

        if node.call_ref.association_trait:
            # 绑定 type params 到 trait
            """
                struct MyConv{item: Int}
                trait DConverter<K, V>{
                    def convert(k: K) -> V;
                }
                
                impl<C1> DConverter<C1, String> for MyConv{
                    def convert(k: C1) -> String{
                        echo("test converter");
                        return "1";
                    }
                }
                
                # 在类型推断阶段，会进行类型变量替换，根据 convert(k) 将 DConverter<C1, String> 替换为 DConverter<K, String>
                # 在代码生成阶段，将根据 convert1 推断真实类型 K: Int
                # 因此还需要将 DConverter<K, String> 替换为 DConverter<Int, String>
                # 对于 target type, function 也做同样的替换
                def convert1<K>(k: K) -> String{
                    return MyConv{item: 1}.convert(k);
                }
                
                let xxxyyxxx = convert1(1);
            """

            trait = type_utils.bind_type(node.call_ref.association_trait, current_context.type_binds)
            func = type_utils.bind_type(node.call_ref, current_context.type_binds)
            trait_name = type_utils.get_type_id(trait)
            target = type_utils.bind_type(node.call_ref.association_type, current_context.type_binds)

            # 编译完成之后的名字，例如:
            compile_name = type_utils.get_trait_function_name(trait, target, source_function_name)
            if compile_name not in self.defined_functions:
                self.function_defs.append(self.visit_function_def(node.define_ast, TypeContext(trait = node.call_ref.association_trait, type_binds=bind_binds, function_name=compile_name, return_type=func.return_type)))
            self.meta_manager.get_or_create_meta(type_utils.get_type_id(target)).vtable[source_function_name][type_utils.get_type_id(trait)] = CodeFunctionObject(lambda *args: eval(compile_name, self.meta_manager.globals)(*args))
        elif node.type_binds:
            compile_name = node.call_source.accept(self) + "___" + "___".join([str(type_utils.get_type_id(x)) for x in bind_binds.values()])
            if compile_name not in self.defined_functions:
                self.function_defs.append(self.visit_function_def(node.define_ast, TypeContext(type_binds=bind_binds, function_name=compile_name, return_type=node.call_ref.return_type)))
                self.defined_functions.add(compile_name)
            function_call_source = compile_name
        else:
            compile_name = node.call_source.accept(self)
            if compile_name not in self.defined_functions:
                self.function_defs.append(self.visit_function_def(node.define_ast, TypeContext(function_name=compile_name, return_type=node.call_ref.return_type)))
                self.defined_functions.add(compile_name)
            function_call_source = compile_name

        arg_str = "(" + ",".join([str(arg.accept(self, TypeContext(type_binds=bind_binds))) for arg in node.args]) + ")"
        #tmp_var = f"tmp_var_{str(uuid4()).replace('-', '_')}"
        if isinstance(node.call_source, AttributeNode) and node.call_ref.association_trait:
            data = node.call_source.data.accept(self, TypeContext(type_binds=bind_binds))
            #data = f"{tmp_var} = {node.call_source.data.accept(self, TypeContext(type_binds=bind_binds))}"
            # 零开销抽象，如果是 primitive type 调用方法且不是动态分派，则会进行转换，这里不用对 primitive 进行包装
            # 例如 1.into，实际上是 into(1)，可以省去装箱开箱的成本
            # if node.call_ref.association_type.is_primitive_type and not node.dyn_dispatch:
            #     function_call_source = f"meta_manager.get_or_create_meta('{node.call_ref.association_type.name}').vtable['{source_function_name}']['{trait_name}']"
            #     arg_str = f"({data},{arg_str[1: -1]})"
            # else:
            #     arg_str = f".get('{trait_name}')({data},{arg_str[1: -1]})"

            if "." in function_call_source:
                parts = function_call_source.split(".")
                call_data = ".".join(parts[0:-1])
                attr = parts[-1]
                tmp_var = f"tmp_var_{str(uuid4()).replace('-', '_')}"
            else:
                tmp_var = f"tmp_var_{str(uuid4()).replace('-', '_')}"
                attr = ""
                call_data = function_call_source
            if node.call_ref.association_type.is_primitive_type and not node.dyn_dispatch:
                function_call_source = f"meta_manager.get_or_create_meta('{node.call_ref.association_type.name}').vtable['{source_function_name}']['{trait_name}']"
                arg_str = f"({data},{arg_str[1: -1]})"
            elif attr:
                return f"({tmp_var}:={call_data}, {tmp_var}.{attr}.get('{trait_name}')({call_data},{arg_str[1: -1]}))[-1]"
            else:
                return f"({tmp_var}:={call_data}, {tmp_var}.get('{trait_name}')({tmp_var},{arg_str[1: -1]}))[-1]"
        return f"{function_call_source}{arg_str}"



    def visit_if(self, node: 'IfStatement', context=None):
        if_branch = node.branches[0]
        elif_branch = node.branches[1:]
        else_branch = node.else_branch
        res = [
            f"if is_true({if_branch[0].accept(self, context)}):",
            if_branch[1].accept(self, context)
       ]

        for condition, branch in elif_branch:
            res.append(f"elif {condition.accept(self)}:")
            res.append(branch.accept(self))
        if else_branch:
            res.append("else:")
            res.append(else_branch.accept(self))
        return "\n".join(res)

    def visit_loop(self, node: 'LoopStatement', context=None):
        pass

    def visit_function_def(self, node: 'FunctionDefNode', context: TypeContext=None):
        current_context = context
        if not context.return_type or not node:
            return ""
        if node.type_parameters and not current_context.type_binds:
            return ""
        if current_context.function_name:
            function_name = current_context.function_name or node.name.string
        else:
            function_name = node.name.string
        args = [x.var_node.string for x in node.args]
        current_context.trait and args.insert(0, "self")
        res = [
                f"def {function_name}({','.join(args)}):",
                node.body.accept(self, context) or "    pass"
            ]
        return "\n".join(res)


    def visit_proc(self, node: 'ProcNode', context=None):
        res = []

        for x in node.children:
            code = x.accept(self, TypeContext())
            if code:
                res.append(code)

        return "\n".join(res)

    def visit_var_def(self, node: 'VarDefNode', context=None):
        # if node.type_ref.name == "" and node.type_ref.constraints:
        #     pass
            #return f"""meta_manager.create_object('{vtable_key}', {data_code})"""
        return f"{node.var_node.string} = {node.init_expr.accept(self, context)}"

    def visit_type(self, node: 'StructNode', context=None):
        pass

    def visit_type_def(self, node: 'StructDefNode', context=None):
        pass

    def create_dyn_object(self, target_type: TypeRef, constraints: List['TraitRef'], binds: Dict[TypeVar, TypeRef]):
        # 遍历所有约束
        for trait in constraints:
            # 传递类型绑定，获取 trait 真实的类型
            target_trait = type_utils.bind_type(trait, binds)
            # 获取所有 impl，编译对应的函数
            for impl in self.trait_impls.get_impl(target_type, target_trait):
                # 如果类型绑定不为空，且有其他类型绑定为目标约束，那同样需要进行编译
                for define_type, bind_type in impl.binds.items():
                    self.create_dyn_object(bind_type, define_type.constraints, binds)
                for func_name, func in impl.functions.items():
                    compile_name = type_utils.get_trait_function_name(trait, target_type, func_name)
                    if compile_name not in self.defined_functions:
                        type_context = TypeContext(trait=target_trait, function_name=compile_name, type_binds=binds,
                                                   return_type=func.return_type)
                        self.function_defs.append(func.association_ast.accept(self, type_context))
                    self.meta_manager.get_or_create_meta(type_utils.get_type_id(target_type)).vtable[func_name][
                        type_utils.get_type_id(trait)] = NameFunctionObject(compile_name, self.meta_manager.globals)

    def visit_return(self, node: 'ReturnNode', context: TypeContext=None):
        """
        如果返回值是一个 trait 的实现，那么需要首先创建 expr type 实现的 trait 所有函数，例如
        def get_dyn() -> dyn TraitA:
            return TypeA{}
        let x = into().xxx();
        此时由于 get_dyn 返回值是一个 dyn TraitA，后续在调用 into().xxx() 时已经不知道原始的类型是什么，首先在 return TypeA{} 时需要将 TypeA 的所有 trait 实现的函数都编译出来，然后在调用 xxx 时可以直接使用这些函数。
        并且，如果是 primitive type 的 trait 实现，那么还需要进行 boxing，例如 1.into()，需要将 1 包装成一个 dyn 对象，然后调用 into() 方法。
        :param node:
        :param context:
        :return:
        """
        expr_type = node.expr_type
        if context.return_type and TypeVar.is_dynamic_trait(context.return_type):
            # 传递类型绑定，获取 return 真实的类型
            target_type = type_utils.bind_type(expr_type, context.type_binds)
            self.create_dyn_object(target_type, context.return_type.constraints, context.type_binds)
            # if target_type.is_primitive_type:
            #     vtable_key = type_utils.get_type_id(expr_type)
            #     return f"""return meta_manager.create_object('{vtable_key}', {node.expr.accept(self, context)})"""
        return f"return {node.expr.accept(self, context)}"

    def visit_identifier(self, node: 'IdNode', context=None):
        pass

    def visit_function_type(self, node: 'FunctionTypeNode', context=None):
        pass

    def visit_attribute(self, node: 'AttributeNode', context=None):
        # tmp_var = f"tmp_var_{str(uuid4())}"
        # data = f"{tmp_var} {node.data.accept(self, context)}"
        return f"{node.data.accept(self, context)}.attr('{node.attr.string}')"

    def visit_trait_function(self, node: 'TraitFunctionNode', context=None):
        super().visit_trait_function(node)

    def visit_trait_def(self, node: 'TraitDefNode', context=None):
        super().visit_trait_def(node)

    def visit_trait_impl(self, node: 'TraitImplNode', context=None):
        target_type_name = node.target_type.name
        #res = []
        # for function in node.functions:
        #     function_name = function.name.string
        #     compile_name = f"__{node.trait.name.string}__{node.target_type.name}__{function_name}"
        #     res.append(function.accept(self))
        #     res.append(f"meta_manager.get_meta('{target_type_name}').vtable['{function_name}'] = {compile_name}")
        #return "\n".join(res)
        return ""


    def visit_trait_node(self, node: 'TraitNode', context=None):
        super().visit_trait_node(node)

    def visit_type_constraint(self, node: 'TraitConstraintNode', context=None):
        super().visit_type_constraint(node)

    def visit_struct_init(self, node: 'StructInitNode', context=None):
        LOGGER.info("visit struct init: %s, %s", context.type_binds, node.type_name.name)
        if node.type_ref.parameters:
            type_ref = type_utils.bind_type(node.type_ref, context.type_binds)
            vtable_key = type_utils.get_type_id(type_ref)
            LOGGER.info("vtable key: %s", vtable_key)
            self.meta_manager.get_or_create_meta(vtable_key)
        else:
            vtable_key = node.type_name.name
            LOGGER.info("vtable key: %s", vtable_key)
            self.meta_manager.get_or_create_meta(vtable_key)
        data_code = "{" + ", ".join([f"'{var.string}': {assign_expr.accept(self, context)}" for var, assign_expr in node.body]) + "}"
        return f"""meta_manager.create_object('{vtable_key}', {data_code})"""