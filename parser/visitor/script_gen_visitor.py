from typing import Dict

from parser.scope import TraitImpls
from runtime.data import MetaManager, CodeFunctionObject, NameFunctionObject
from code_gen.script import PythonCodeGenerator
from parser.node import *
from parser import utils
from dataclasses import dataclass, field
from parser.visitor import utils as type_utils

@dataclass
class TypeContext:
    trait_impl: Optional[TraitImpl] = None
    type_binds: Dict['TypeVar', TypeRef] = field(default_factory=dict)
    function_name: Optional[str] = None

class EvalVisitor(Visitor):
    def __init__(self, meta_manager: MetaManager, code_generator: PythonCodeGenerator, trait_impl: TraitImpls):
        self.meta_manager = meta_manager
        self.code_gen = code_generator
        self.defined_functions = set()
        self.type_contexts: List[TypeContext] = []
        self.function_defs = ["def echo(*args): print(*args)", "def as_string(*args): return str(*args)", "def as_float(*args): return float(*args)"]
        self.trait_impls = trait_impl

    def visit_bin_op(self, node: 'BinaryOpNode'):
        left = node.left.accept(self)
        right = node.right.accept(self)
        return f"{left} {node.op} {right}"

    def visit_assign(self, node: 'AssignNode'):
        return f"{node.var.identifier.string}={node.assign_expr.accept(self)}"

    def visit_lit(self, node: 'LiteralNode'):
        match node.literal_type.lower():
            case "float": return float(node.val)
            case "int": return int(node.val)
            case "bool": return bool(node.val)
            case _: return node.val

    def visit_var(self, node: 'VarNode'):
        return node.identifier.string

    def visit_block(self, node: 'BlockNode'):
        res = "\n".join([utils.indent(stmt.accept(self), 1)   for stmt in node.stmts] )
        return res

    def visit_function_call(self, node: 'FunctionCallNode'):
        function_name = ""
        # 如果这个函数是某个 trait 的实现
        trait_name = ""
        function_call_source = node.call_source.accept(self)
        if node.trait_impl:
            trait = type_utils.bind_type(node.trait_impl.trait, self.type_contexts[-1].type_binds)
            trait_name = type_utils.get_type_id(trait)
            target = type_utils.bind_type(node.trait_impl.target_type, self.type_contexts[-1].type_binds)
            trait_function_name = node.define_ast.name.string
            # 编译完成之后的名字，例如:
            # impl Trait<String> for Target<String, Int> xxx function
            # 会被编译为 Trait_p_String_q___Target_p_String_Int_q___xxxx

            bind_binds = type_utils.resolve_type_binds(node.type_binds,
                                                       self.type_contexts[-1].type_binds) if self.type_contexts and \
                                                                                             self.type_contexts[
                                                                                                 -1].type_binds else node.type_binds
            for type_var, bind_type in bind_binds.items():
                for const in type_var.constraints:
                    impl = self.trait_impls.get_impl(bind_type, const)
                    for name, func in impl.functions.items():
                        compile_name = type_utils.get_trait_function_name(const, bind_type, func.name)
                        type_context = TypeContext(trait_impl=impl, function_name=compile_name, type_binds=bind_binds)
                        if bind_type.is_primitive_type:
                            self.meta_manager.get_or_create_meta(bind_type.name).vtable[func.name][
                                type_utils.get_type_id(const)] = NameFunctionObject(compile_name,
                                                                                    self.meta_manager.globals)
                        self.type_contexts.append(type_context)
                        self.function_defs.append(func.association_ast.accept(self))
                        self.type_contexts.pop(-1)
            compile_name = type_utils.get_trait_function_name(trait, target, trait_function_name)
            self.type_contexts.append(TypeContext(trait_impl=node.trait_impl, type_binds=bind_binds, function_name=compile_name))
            self.function_defs.append(self.visit_function_def(node.define_ast))
            self.meta_manager.get_or_create_meta(type_utils.get_type_id(target)).vtable[trait_function_name][type_utils.get_type_id(trait)] = CodeFunctionObject(lambda *args: eval(compile_name, self.meta_manager.globals)(*args))
            self.type_contexts.pop(-1)
        elif node.type_binds:
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
            bind_binds = type_utils.resolve_type_binds(node.type_binds, self.type_contexts[-1].type_binds) if self.type_contexts and self.type_contexts[-1].type_binds else node.type_binds
            for type_var, bind_type in bind_binds.items():
                for const in type_var.constraints:
                    impl = self.trait_impls.get_impl(bind_type, const)
                    for name, func in impl.functions.items():
                        compile_name = type_utils.get_trait_function_name(const, bind_type, func.name)
                        type_context = TypeContext(trait_impl=impl, function_name=compile_name, type_binds=bind_binds)
                        if bind_type.is_primitive_type:
                            self.meta_manager.get_or_create_meta(bind_type.name).vtable[func.name][type_utils.get_type_id(const)] = NameFunctionObject(compile_name, self.meta_manager.globals)
                        self.type_contexts.append(type_context)
                        self.function_defs.append(func.association_ast.accept(self))
                        self.type_contexts.pop(-1)
            compile_name =  node.call_source.accept(self) + "___" + "___".join([str(type_utils.get_type_id(x)) for x in bind_binds.values()])
            if compile_name not in self.defined_functions:
                self.type_contexts.append(TypeContext(type_binds=bind_binds, function_name=compile_name))
                self.function_defs.append(self.visit_function_def(node.define_ast))
                self.type_contexts.pop(-1)
                self.defined_functions.add(compile_name)
            function_call_source = compile_name
        elif node.dyn_trait:
            pass
            #pass
            # compile_name = self.trait_impls.get_impl_by_type(bind_type)
            # type_context = TypeContext(trait_impl=impl, function_name=compile_name, type_binds=bind_binds)
            # if bind_type.is_primitive_type:
            #     self.meta_manager.get_or_create_meta(bind_type.name).vtable[func.name][
            #         type_utils.get_type_id(const)] = NameFunctionObject(compile_name, self.meta_manager.globals)
            # self.type_contexts.append(type_context)
            # self.function_defs.append(func.association_ast.accept(self))
            # self.type_contexts.pop(-1)


        #self.type_contexts.append(TypeContext(type_binds=node.type_binds))
        arg_str = "(" + ",".join([str(arg.accept(self)) for arg in node.args]) + ")"
        if isinstance(node.call_source, AttributeNode) and (node.trait_impl or node.dyn_trait):
            data = node.call_source.data.accept(self)
            if node.call_ref.call_source_type:
                type_ref = type_utils.bind_type(node.call_ref.call_source_type, self.type_contexts[-1].type_binds)
                trait_name = trait_name or type_utils.get_type_id(node.dyn_trait)
                if type_ref.is_primitive_type:
                    function_call_source = f"meta_manager.get_or_create_meta('{type_ref.name}').vtable['{node.call_source.attr.string}']['{trait_name}']"
                    arg_str = f"({data},{arg_str[1: -1]})"
                else: arg_str = f".get('{trait_name}')({data},{arg_str[1: -1]})"
            else:
                arg_str = f".get('{trait_name}')({data},{arg_str[1: -1]})"
        return f"{function_call_source}{arg_str}"



    def visit_if(self, node: 'IfStatement'):
        if_branch = node.branches[0]
        elif_branch = node.branches[1:]
        else_branch = node.else_branch
        res = [
            f"if {if_branch[0].accept(self)}:",
            if_branch[1].accept(self)
       ]

        for condition, branch in elif_branch:
            res.append(f"elif {condition.accept(self)}:")
            res.append(branch.accept(self))
        if else_branch:
            res.append("else:")
            res.append(else_branch.accept(self))
        return "\n".join(res)

    def visit_loop(self, node: 'LoopStatement'):
        pass

    def visit_function_def(self, node: 'FunctionDefNode'):
        current_context = self.type_contexts[-1]
        if node.type_parameters and not current_context.type_binds:
            return ""
        if current_context.function_name:
            function_name = current_context.function_name or node.name.string
        else:
            function_name = node.name.string
        args = [x.var_node.string for x in node.args]
        current_context.trait_impl and args.insert(0, "self")
        res = [
                f"def {function_name}({','.join(args)}):",
                node.body.accept(self)
            ]
        return "\n".join(res)


    def visit_proc(self, node: 'ProcNode'):
        res = []
        self.type_contexts.append(TypeContext())
        for x in node.children:
            code = x.accept(self)
            if code:
                res.append(code)
        self.type_contexts.pop(-1)
        return "\n".join(res)

    def visit_var_def(self, node: 'VarDefNode'):
        # if node.type_ref.name == "" and node.type_ref.constraints:
        #     pass
            #return f"""meta_manager.create_object('{vtable_key}', {data_code})"""
        return f"{node.var_node.string} = {node.init_expr.accept(self)}"

    def visit_type(self, node: 'StructNode'):
        pass

    def visit_type_def(self, node: 'StructDefNode'):
        #self.meta_manager.add_meta(DataMeta(node.type_name.string))
        pass

    def visit_return(self, node: 'ReturnNode'):
        expr_type = node.expr_type
        expect_type = node.expect_type
        if expect_type and expect_type.name == "ANON_TYPE_VAR":
            for trait in expect_type.constraints:
                for impl in self.trait_impls.get_impl_by_type(expr_type):
                    for func_name, func in impl.functions.items():
                        compile_name = type_utils.get_trait_function_name(trait, expr_type, func_name)
                        type_context = TypeContext(trait_impl=impl, function_name=compile_name, type_binds={})
                        self.type_contexts.append(type_context)
                        self.function_defs.append(self.visit_function_def(func.association_ast))
                        self.type_contexts.pop(-1)
                        self.meta_manager.get_or_create_meta(type_utils.get_type_id(expr_type)).vtable[func_name][type_utils.get_type_id(trait)] = NameFunctionObject(compile_name, self.meta_manager.globals)
            vtable_key = type_utils.get_type_id(expr_type)
            return f"""return meta_manager.create_object('{vtable_key}', {node.expr.accept(self)})"""

        return f"return {node.expr.accept(self)}"

    def visit_identifier(self, node: 'IdNode'):
        pass

    def visit_function_type(self, node: 'FunctionTypeNode'):
        pass

    def visit_attribute(self, node: 'AttributeNode'):
        return f"{node.data.accept(self)}.attr('{node.attr.string}')"

    def visit_trait_function(self, node: 'TraitFunctionNode'):
        super().visit_trait_function(node)

    def visit_trait_def(self, node: 'TraitDefNode'):
        super().visit_trait_def(node)

    def visit_trait_impl(self, node: 'TraitImplNode'):
        target_type_name = node.target_type.name
        #res = []
        # for function in node.functions:
        #     function_name = function.name.string
        #     compile_name = f"__{node.trait.name.string}__{node.target_type.name}__{function_name}"
        #     res.append(function.accept(self))
        #     res.append(f"meta_manager.get_meta('{target_type_name}').vtable['{function_name}'] = {compile_name}")
        #return "\n".join(res)
        return ""


    def visit_trait_node(self, node: 'TraitNode'):
        super().visit_trait_node(node)

    def visit_type_constraint(self, node: 'TraitConstraintNode'):
        super().visit_type_constraint(node)

    def visit_struct_init(self, node: 'StructInitNode'):
        context = self.type_contexts[-1]
        if node.type_ref.parameters:
            type_ref = type_utils.bind_type(node.type_ref, context.type_binds)
            vtable_key = type_utils.get_type_id(type_ref)
            self.meta_manager.get_or_create_meta(vtable_key)
        else:
            vtable_key = node.type_name.name
            self.meta_manager.get_or_create_meta(vtable_key)
        data_code = "{" + ", ".join([f"'{var.string}': {assign_expr.accept(self)}" for var, assign_expr in node.body]) + "}"
        return f"""meta_manager.create_object('{vtable_key}', {data_code})"""