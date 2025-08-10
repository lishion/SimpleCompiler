from parser.node import *

class Visitor[T]:
   
    def visit_bin_op(self, node: 'BinaryOpNode', parse_context: T|None=None):
        return None

   
    def visit_assign(self, node: 'AssignNode', parse_context: T|None=None):
        return None

   
    def visit_lit(self, node: 'LiteralNode', parse_context: T|None=None):
        return None

   
    def visit_var(self, node: 'VarNode', parse_context: T|None=None):
        return None

   
    def visit_block(self, node: 'BlockNode', parse_context: T|None=None):
        return None

   
    def visit_function_call(self, node: 'FunctionCallNode', parse_context: T|None=None):
        return None

   
    def visit_if(self, node: 'IfStatement', parse_context: T|None=None):
        return None

   
    def visit_loop(self, node: 'LoopStatement', parse_context: T|None=None):
        return None

   
    def visit_function_def(self, node: 'FunctionDefNode', parse_context: T|None=None):
        return None

   
    def visit_proc(self, node: 'ProcNode', parse_context: T|None=None):
        for child in node.children:
            child.accept(self, None)

   
    def visit_var_def(self, node: 'VarDefNode', parse_context: T|None=None):
        return None

   
    def visit_type(self, node: 'StructNode', parse_context: T|None=None):
        return None

   
    def visit_struct_def(self, node: 'StructNode', parse_context: T|None=None):
        return None

   
    def visit_return(self, node: 'ReturnNode', parse_context: T|None=None):
        return None

   
    def visit_identifier(self, node: 'IdNode', parse_context: T|None=None):
        return None

   
    def visit_struct_init(self, node: 'StructInitNode', parse_context: T|None=None):
        return None

   
    def visit_function_type(self, node: 'FunctionTypeNode', parse_context: T|None=None):
        return None

    def visit_trait_function(self, node: 'TraitFunctionNode', parse_context: T|None=None):
        return None

    def visit_trait_def(self, node: 'TraitDefNode', parse_context: T|None=None):
        pass

    def visit_trait_impl(self, node: 'TraitImplNode', parse_context: T|None=None):
        pass

    def visit_trait_node(self, node: 'TraitNode', parse_context: T|None=None):
        pass

    def visit_attribute(self, node: 'AttributeNode', parse_context: T|None=None):
        pass

    def visit_type_constraint(self, node: 'TraitConstraintNode', parse_context: T|None=None):
        pass

    def visit_continue_or_break(self, node: 'ContinueOrBreak', parse_context: T|None=None):
        pass

    def visit_generic_type(self, node: 'GenericTypeNode', parse_context: T|None=None):
        pass

    def visit_type_var(self, node: 'TypeVarNode', parse_context: T|None=None):
        pass

    def visit_type_annotation(self, node: 'TypeAnnotation', parse_context: T|None=None):
        pass

    def visit_type_instance(self, node: 'TypeInstance', parse_context: T|None=None):
        pass

    def visit_dyn_trait(self, node: 'DynTraitNode', parse_context: T|None=None):
        pass

    def visit_trait_constraint(self, node: 'TraitConstraintNode', parse_context: T|None=None):
        pass

    def visit_for(self, node: 'ForNode', parse_context: T|None=None):
        pass

    def visit_logic_not(self, node: 'LogicNotNode', parse_context: T|None=None):
        return None

    def visit_bitwise_not(self, node: 'BitwiseNotNode', parse_context: T|None=None):
        return None