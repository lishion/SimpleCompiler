from parser.node import *

class Visitor[T]:
   
    def visit_bin_op(self, node: 'BinaryOpNode'):
        return None

   
    def visit_assign(self, node: 'AssignNode'):
        return None

   
    def visit_lit(self, node: 'LiteralNode'):
        return None

   
    def visit_var(self, node: 'VarNode'):
        return None

   
    def visit_block(self, node: 'BlockNode'):
        return None

   
    def visit_function_call(self, node: 'FunctionCallNode'):
        return None

   
    def visit_if(self, node: 'IfStatement'):
        return None

   
    def visit_loop(self, node: 'LoopStatement'):
        return None

   
    def visit_function_def(self, node: 'FunctionDefNode'):
        return None

   
    def visit_proc(self, node: 'ProcNode'):
        for child in node.children:
            child.accept(self)

   
    def visit_var_def(self, node: 'VarDefNode'):
        return None

   
    def visit_type(self, node: 'StructNode'):
        return None

   
    def visit_struct_def(self, node: 'StructNode'):
        return None

   
    def visit_return(self, node: 'ReturnNode'):
        return None

   
    def visit_identifier(self, node: 'IdNode'):
        return None

   
    def visit_struct_init(self, node: 'StructInitNode'):
        return None

   
    def visit_function_type(self, node: 'FunctionTypeNode'):
        return None

    def visit_trait_function(self, node: 'TraitFunctionNode'):
        return None

    def visit_trait_def(self, node: 'TraitDefNode'):
        pass

    def visit_trait_impl(self, node: 'TraitImplNode'):
        pass

    def visit_trait_node(self, node: 'TraitNode'):
        pass

    def visit_attribute(self, node: 'AttributeNode'):
        pass

    def visit_type_constraint(self, node: 'TraitConstraintNode'):
        pass

    def visit_continue_or_break(self, node: 'ContinueOrBreak'):
        pass

    def visit_generic_type(self, node: 'GenericTypeNode'):
        pass

    def visit_type_var(self, node: 'TypeVarNode'):
        pass

    def visit_type_annotation(self, node: 'TypeAnnotation'):
        pass

    def visit_type_instance(self, node: 'TypeInstance'):
        pass

    def visit_dyn_trait(self, node: 'DynTraitNode'):
        pass

    def visit_trait_constraint(self, node: 'TraitConstraintNode'):
        pass