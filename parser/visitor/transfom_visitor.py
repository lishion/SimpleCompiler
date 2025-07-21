from parser.visitor.visitor import Visitor
from parser.node import *

class TransformVisitor(Visitor):

    def __init__(self, type_visitor):
        super().__init__()
        self.type_visitor = type_visitor

    def visit_var_def(self, node: 'VarDefNode', parse_context=None):
        node.init_expr = node.init_expr.accept(self, parse_context) or node.init_expr

    def visit_bin_op(self, node: 'BinaryOpNode', parse_context=None):
        left = node.left.accept(self, parse_context) or node.left
        right = node.right.accept(self, parse_context) or node.right
        if node.op == "+":
            call_source = AttributeNode(left, IdNode("add"))
            call_source.scope = node.scope
            new_node = FunctionCallNode(
                call_source=call_source,
                args=[right]
            )
            new_node.scope = node.scope
            self.type_visitor.visit_function_call(new_node, parse_context)
            return new_node
        return None
        #node.left = node.left.accept(self, parse_context) or node.left