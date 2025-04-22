from abc import ABC

from parser.node import *
from abc import ABC, abstractmethod

@abstractmethod
class Visitor(ABC):
    @abstractmethod
    def visit_bin_op(self, node: 'BinaryOpNode'): pass

    @abstractmethod
    def visit_assign(self, node: 'AssignNode'): pass

    @abstractmethod
    def visit_lit(self, node: 'LiteralNode'): pass

    @abstractmethod
    def visit_var(self, node: 'VarNode'): pass

    @abstractmethod
    def visit_block(self, node: 'BlockNode'): pass

    @abstractmethod
    def visit_function_call(self, node: 'FunctionCallNode'): pass

    @abstractmethod
    def visit_if(self, node: 'IfStatement'): pass

    @abstractmethod
    def visit_loop(self, node: 'LoopStatement'): pass

    @abstractmethod
    def visit_funcdef(self, node: 'FuncDefStatement'): pass

    @abstractmethod
    def visit_proc(self, node: 'ProcNode'): pass



class PrintVisitor(Visitor, ABC):

    def visit_bin_op(self, node: 'BinaryOpNode'):
        print(node.__class__.__name__)
        print(node.left.visit(self))
        print(node.right.visit(self))

    def visit_assign(self, node: 'AssignNode'):
        print(node.__class__.__name__)
        print(node.left.visit(self))
        print(node.right.visit(self))

    def visit_lit(self, node: 'LiteralNode'):
        print(node.__class__.__name__)
        print(node.val)

    def visit_var(self, node: 'VarNode'):
        print(node.__class__.__name__)
        print(node.name)

    def visit_block(self, node: 'BlockNode'):
        print(node.__class__.__name__)
        for stmt in node.stmts:
            print(stmt.visit(this))

    def visit_function_call(self, node: 'FunctionCallNode'):
        print(node.__class__.__name__)
        print(node.function_name)

    def visit_if(self, node: 'IfStatement'):
        print(node.__class__.__name__)
        print(node.branches)

    def visit_loop(self, node: 'LoopStatement'):
        print(node.__class__.__name__)
        print(node.body)

    def visit_funcdef(self, node: 'FuncDefStatement'):
        print(node.__class__.__name__)
        print(node.args)

    def visit_proc(self, node: 'ProcNode'):
        print(node.__class__.__name__)
        for child in node.children:
            print(child.visit(self))