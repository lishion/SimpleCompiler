from error.reporter import ErrorReporter
from parser.cfg.return_check import check_return
from parser.cfg.cfg_node import BasicBlock
from parser.node import *

class CFGVisitor(Visitor):

    def __init__(self, reporter):
        self.reporter: ErrorReporter = reporter

    def visit_bin_op(self, node: 'BinaryOpNode'):
        pass

    def visit_assign(self, node: 'AssignNode'):
        pass

    def visit_lit(self, node: 'LiteralNode'):
        pass

    def visit_var(self, node: 'VarNode'):
        pass

    def visit_block(self, node: 'BlockNode'):
        current = init_block = BasicBlock()
        for stmt in node.stmts:
            match stmt:
                case IfStatement() | LoopStatement():
                    entry_block, exit_block = stmt.accept(self)
                    current.next_blocks.append(entry_block)
                    current = BasicBlock()
                    exit_block.next_blocks.append(current)
                case _:
                    current.instructions.append(stmt)
        return init_block, current

    def visit_if(self, node: 'IfStatement'):
        current = entry_block = BasicBlock()
        exit_block = BasicBlock()
        for branch, body in node.branches:
            branch_block = BasicBlock()
            current.next_blocks.append(branch_block)

            body_entry_block, body_exist_block = body.accept(self)
            body_exist_block.next_blocks.append(exit_block)

            branch_block.instructions.append(branch)
            branch_block.next_blocks.append(body_entry_block)

            current = branch_block
        if node.else_branch:
            body_entry_block, body_exist_block = node.else_branch.accept(self)
            body_exist_block.next_blocks.append(exit_block)
            current.next_blocks.append(body_entry_block)

        return entry_block, exit_block

    def visit_loop(self, node: 'LoopStatement'):
        entry_block = BasicBlock()
        body_entry_block, body_exit_block = node.body.accept(self)
        entry_block.instructions.append(node.condition)
        entry_block.next_blocks.append(body_entry_block)
        entry_block.next_blocks.append(body_exit_block)
        return entry_block, body_exit_block

    def visit_function_def(self, node: 'FunctionDefNode'):
        return node.body.accept(self)

    def visit_proc(self, node: 'ProcNode'):
        for stmt in node.children:
            if isinstance(stmt, FunctionDefNode):
                entry_node, _ = stmt.accept(self)
                if check_return(entry_node):
                    raise TypeError("missing return statement\n" + self.reporter.mark(stmt.name))

    def visit_var_def(self, node: 'VarDefNode'):
        pass

    def visit_type(self, node: 'StructNode'):
        pass

    def visit_type_def(self, node: 'StructNode'):
        pass

    def visit_return(self, node: 'ReturnNode'):
        pass

    def visit_identifier(self, node: 'IdNode'):
        pass

    def visit_struct_init(self, node: 'StructInitNode'):
        pass

    def visit_function_type(self, node: 'FunctionTypeNode'):
        pass

    def visit_trait_function(self, node: 'TraitFunctionNode'):
        super().visit_trait_function(node)

    def visit_trait_def(self, node: 'TraitDefNode'):
        super().visit_trait_def(node)

    def visit_trait_impl(self, node: 'TraitImplNode'):
        super().visit_trait_impl(node)

    def visit_trait_node(self, node: 'TraitNode'):
        super().visit_trait_node(node)

    def visit_attribute(self, node: 'AttributeNode'):
        super().visit_attribute(node)

    def visit_type_constraint(self, node: 'TraitConstraintNode'):
        super().visit_type_constraint(node)

    def visit_continue_or_break(self, node: 'ContinueOrBreak'):
        super().visit_continue_or_break(node)

    def visit_function_call(self, node: 'FunctionCallNode'):
        pass

