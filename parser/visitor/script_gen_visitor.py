from typing import Dict

from parser.scope import TraitImpls
from runtime.data import MetaManager, CodeFunctionObject
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
        self.function_defs = []
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
        if node.trait_impl:
            trait = type_utils.bind_type(node.trait_impl.trait, self.type_contexts[-1].type_binds)
            target = type_utils.bind_type(node.trait_impl.target_type, self.type_contexts[-1].type_binds)
            function_name = type_utils.get_trait_function_name(trait, target, node.define_ast.name.string)
            self.type_contexts.append(TypeContext(trait_impl=node.trait_impl, type_binds=node.type_binds, function_name=function_name))
            self.function_defs.append(self.visit_function_def(node.define_ast))
            self.meta_manager.metas[type_utils.get_type_id(target)].vtable[node.define_ast.name.string][type_utils.get_type_id(trait)] = CodeFunctionObject(lambda *args: eval(function_name, self.meta_manager.globals)(*args))
            self.type_contexts.pop(-1)
        elif node.type_binds:
            function_name =  "_".join([str(x) for x in node.type_binds.values()]).replace("<", "$_").replace(">", "_$")
            if function_name not in self.defined_functions:
                self.type_contexts.append(TypeContext(type_binds=node.type_binds, function_name=node.call_source.accept(self) + "___" + function_name))
                self.function_defs.append(self.visit_function_def(node.define_ast))
                self.type_contexts.pop(-1)
                self.defined_functions.add(function_name)
        else:
            self.type_contexts.append(TypeContext())
        if not node.trait_impl and node.type_binds:
            function_call_source = node.call_source.accept(self) + "___" + function_name
        else:
            function_call_source = node.call_source.accept(self)
        arg_str = "(" + ",".join([str(var.accept(self)) for var in node.args]) + ")"
        if isinstance(node.call_source, AttributeNode) and node.trait_impl:
            trait_name = type_utils.get_type_id(node.trait_impl.trait)
            data = node.call_source.data.accept(self)
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
        return f"{node.var_node.string} = {node.init_expr.accept(self)}"

    def visit_type(self, node: 'StructNode'):
        pass

    def visit_type_def(self, node: 'StructDefNode'):
        #self.meta_manager.add_meta(DataMeta(node.type_name.string))
        pass

    def visit_return(self, node: 'ReturnNode'):
        return f"return {node.expr.accept(self)}"

    def visit_identifier(self, node: 'IdNode'):
        pass

    def visit_type_init(self, node: 'StructInitNode'):
        data_code = "{" + ", ".join([f"'{var.string}':{assign_expr.accept(self)}" for var, assign_expr in node.body]) + "}"
        return f"""meta_manager.create_object('{node.type_name.name}', {data_code})"""

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