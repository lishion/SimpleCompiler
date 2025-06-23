from code_gen.script import PythonCodeGenerator
from error.exception import UndefinedError, DuplicateDefineError, TypeConstraintError, TypeError
from parser.stack import Stack
from parser.symbol import VarSymbol, TypeSymbol, FunctionSymbol, Symbol, TBDSymbol, TraitSymbol
from parser.node import *
from abc import ABC, abstractmethod
from parser.types import VarType, FunctionSignature, Type, BaseType, TraitConstraintsType, UNIT, TypeVar
from error.reporter import ErrorReporter
from parser import utils

from runtime.data import MetaManager, DataMeta
from itertools import zip_longest


@abstractmethod
class Visitor(ABC):
    @abstractmethod
    def visit_bin_op(self, node: 'BinaryOpNode'):
        return None

    @abstractmethod
    def visit_assign(self, node: 'AssignNode'):
        return None

    @abstractmethod
    def visit_lit(self, node: 'LiteralNode'):
        return None

    @abstractmethod
    def visit_var(self, node: 'VarNode'):
        return None

    @abstractmethod
    def visit_block(self, node: 'BlockNode'):
        return None

    @abstractmethod
    def visit_function_call(self, node: 'FunctionCallNode'):
        return None

    @abstractmethod
    def visit_if(self, node: 'IfStatement'):
        return None

    @abstractmethod
    def visit_loop(self, node: 'LoopStatement'):
        return None

    @abstractmethod
    def visit_function_def(self, node: 'FunctionDefNode'):
        return None

    @abstractmethod
    def visit_proc(self, node: 'ProcNode'):
        return None

    @abstractmethod
    def visit_var_def(self, node: 'VarDefNode'):
        return None

    @abstractmethod
    def visit_type(self, node: 'StructNode'):
        return None

    @abstractmethod
    def visit_type_def(self, node: 'StructNode'):
        return None

    @abstractmethod
    def visit_return(self, node: 'ReturnNode'):
        return None

    @abstractmethod
    def visit_identifier(self, node: 'IdNode'):
        return None

    @abstractmethod
    def visit_type_init(self, node: 'StructInitNode'):
        return None

    @abstractmethod
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

class PositionVisitor(Visitor):

    def visit_bin_op(self, node: 'BinaryOpNode'):
        node.start_pos, node.end_pos = node.left.accept(self)[0], node.right.accept(self)[1]
        return node.start_pos, node.end_pos

    def visit_assign(self, node: 'AssignNode'):
        node.start_pos, node.end_pos = node.var.accept(self)[0], node.assign_expr.accept(self)[1]
        return node.start_pos, node.end_pos

    def visit_lit(self, node: 'LiteralNode'):
        return node.start_pos, node.end_pos

    def visit_var(self, node: 'VarNode'):
        node.start_pos, node.end_pos = node.identifier.accept(self)
        return node.identifier.start_pos, node.identifier.end_pos

    def visit_block(self, node: 'BlockNode'):
        for stmt in node.stmts:
            stmt.accept(self)
        if node.stmts:
            node.start_pos, node.end_pos = node.stmts[0].accept(self)[0], node.stmts[-1].accept(self)[-1]
        else:
            node.start_pos, node.end_pos = None, None
        return node.start_pos, node.end_pos

    def visit_function_call(self, node: 'FunctionCallNode'):
        node.start_pos, node.end_pos = node.call_source.accept(self)
        for arg in node.args:
            arg.accept(self)
        return node.start_pos, node.end_pos

    def visit_if(self, node: 'IfStatement'):
        node.start_pos, node.end_pos = node.branches[0][0].accept(self)
        for condition, statement in node.branches:
            condition.accept(self)
            statement.accept(self)
        if node.else_branch:
            node.end_pos = node.else_branch.accept(self)[1]
        return node.start_pos, node.end_pos

    def visit_loop(self, node: 'LoopStatement'):
        s1, e1 =  node.condition.accept(self)
        s2, e2 = node.body.accept(self)
        node.start_pos, node.end_pos = s1, e2
        return node.start_pos, node.end_pos

    def visit_function_def(self, node: 'FunctionDefNode'):
        node.start_pos, node.end_pos = node.name.accept(self)
        if node.body.stmts:
            for stmt in node.body.stmts:
                stmt.accept(self)
            node.end_pos = stmt.end_pos
        return node.start_pos, node.end_pos

    def visit_proc(self, node: 'ProcNode'):
        for child in node.children:
            child.accept(self)

    def visit_var_def(self, node: 'VarDefNode'):
        node.start_pos, node.end_pos = node.var_node.accept(self)
        node.var_type and node.var_type.accept(self)
        end = None
        if node.init_expr:
            _, end = node.init_expr.accept(self)
        if end:
            node.end_pos = end
        return node.start_pos, node.end_pos

    def visit_type(self, node: 'StructNode'):
        return node.start_pos, node.end_pos

    def visit_type_def(self, node: 'StructDefNode'):
        start_pos = node.name_and_param.accept(self)[0]
        end_pos = [(name.accept(self), d.accept(self)) for name, d in node.fields]
        node.start_pos, node.end_pos = start_pos, end_pos[-1][1]
        return node.start_pos, node.end_pos

    def visit_return(self, node: 'ReturnNode'):
        if node.expr:
            _, node.end_pos = node.expr.accept(self)
        return node.start_pos, node.end_pos

    def visit_identifier(self, node: 'IdNode'):
        return node.start_pos, node.end_pos

    def visit_type_init(self, node: 'StructInitNode'):
        node.start_pos, node.end_pos = node.type_name.accept(self)
        for expr in node.body:
            expr.accept(self)
        node.end_pos = node.body[-1].accept(self)[1]
        return node.start_pos, node.end_pos

    def visit_function_type(self, node: 'FunctionTypeNode'):
        for arg_type in node.args:
            arg_type.accept(self)
        node.return_type.accept(self)
        node.start_pos, node.end_pos = node.return_type.accept(self)
        return node.start_pos, node.end_pos

    def visit_trait_function(self, node: 'TraitFunctionNode'):
        for arg in node.args:
            arg.accept(self)
        node.start_pos = node.args[0].accept(self)[0]
        node.end_pos = node.args[-1].accept(self)[1]
        return node.start_pos, node.end_pos

    def visit_trait_def(self, node: 'TraitDefNode'):
        node.start_pos, node.end_pos = node.name_and_param.accept(self)
        node.type_var.accept(self)
        for function in node.functions:
            node.end_pos = function.accept(self)[-1]
        return node.start_pos, node.end_pos

    def visit_trait_impl(self, node: 'TraitImplNode'):
        node.trait.accept(self)
        node.target_type.accept(self)
        for function in node.functions:
            function.accept(self)
        return node.start_pos, node.end_pos

    def visit_trait_node(self, node: 'TraitNode'):
        node.start_pos, node.end_pos = node.name.accept(self)
        return node.start_pos, node.end_pos

    def visit_attribute(self, node: 'AttributeNode'):
        node.start_pos = node.data.accept(self)[0]
        node.end_pos = node.attr.accept(self)[1]
        return node.start_pos, node.end_pos

    def visit_type_constraint(self, node: 'TraitConstraintNode'):
        for trait in node.traits:
            trait.accept(self)
        node.start_pos = node.traits[0].accept(self)[0]
        node.end_pos = node.traits[-1].accept(self)[1]
        return node.start_pos, node.end_pos

    def visit_continue_or_break(self, node: 'ContinueOrBreak'):
        return node.start_pos, node.end_pos

    def visit_type_annotation(self, node: 'TypeAnnotation'):
        return node.start_pos, node.end_pos




class SymbolVisitor(Visitor):
    
    def __init__(self, scope_manager: 'ScopeManager', reporter: ErrorReporter):
        self.scope_manager = scope_manager
        self.reporter = reporter
        self.inside_function = False
        self.inside_loop = False

    def visit_bin_op(self, node: 'BinaryOpNode'):
        node.left.accept(self)
        node.right.accept(self)

    def visit_assign(self, node: 'AssignNode'):
        node.scope = self.scope_manager.current_scope
        node.assign_expr.accept(self)
        node.var.accept(self)

    def visit_lit(self, node: 'LiteralNode'):
        pass

    def visit_var(self, node: 'VarNode'):
        node.scope = self.scope_manager.current_scope
        node.identifier.accept(self)

    def add_symbol(self, symbol: Symbol, ast: ASTNode):
        try:
            if type(symbol) in (VarSymbol, FunctionSymbol, TBDSymbol):
                self.scope_manager.current_scope.add_var(symbol)
            elif type(symbol) is TypeSymbol:
                self.scope_manager.add_struct(symbol)
            elif type(symbol) is TraitSymbol:
                self.scope_manager.add_trait(symbol)
            else:
                utils.died_branch()
        except DuplicateDefineError as e:
            message = e.message
            raise DuplicateDefineError((message + "\n") + self.reporter.mark(ast))

    def visit_var_def(self, node: 'VarDefNode'):
        node.scope = self.scope_manager.current_scope
        node.var_node.accept(self)
        node.var_type and node.var_type.accept(self)
        node.init_expr and node.init_expr.accept(self)
        # 可能是函数/变量/Trait，先使用 TBDSymbol 占位
        self.add_symbol(TBDSymbol(node.var_node.string), node)


    def visit_block(self, node: 'BlockNode'):
        node.scope = self.scope_manager.current_scope
        with self.scope_manager.new_scope():
            for stmt in node.stmts:
                stmt.accept(self)


    def visit_function_call(self, node: 'FunctionCallNode'):
        node.scope = self.scope_manager.current_scope
        node.call_source.accept(self)
        for arg in node.args:
            arg.accept(self)

    def visit_if(self, node: 'IfStatement'):
        for condition, body in node.branches:
            condition.accept(self)
            body.accept(self)
        node.else_branch and node.else_branch.accept(self)

    def visit_loop(self, node: 'LoopStatement'):
        self.inside_loop = True
        node.scope = self.scope_manager.current_scope
        node.condition.accept(self)
        node.body.accept(self)
        with self.scope_manager.new_scope() as scope:
            node.body.accept(self)
        self.inside_loop = False


    def visit_function_def(self, node: 'FunctionDefNode'):
        node.scope = self.scope_manager.current_scope
        func = FunctionSymbol(node.name.string, utils.extract_type_from_ast(node), func_def=node)
        self.scope_manager.add_var(func)
        self.inside_function = True
        with self.scope_manager.new_scope():
            for arg in node.args:
                arg.accept(self)
            node.body.accept(self)
            node.return_type.accept(self)
        self.inside_function = False


    def visit_proc(self, node: 'ProcNode'):
        for child in node.children:
            child.accept(self)

    def visit_type(self, node: 'StructNode'):
        node.scope = self.scope_manager.current_scope
        # if not node.scope.lookup_type(node.name):
        #     self.reporter.add_undefined_error_by_ast(node.name, node)

    def visit_type_def(self, node: 'StructDefNode'):
        symbol = TypeSymbol(node.name_and_param.name, type_def_ast=node)
        self.add_symbol(symbol, node)
        node.scope = self.scope_manager.current_scope
        with self.scope_manager.new_scope():
            for type_var in node.name_and_param.parameters:
                type_var.accept(self)
            for _, type_node in node.fields:
                type_node.accept(self)

    def visit_return(self, node: 'ReturnNode'):
        if not self.inside_function:
            raise Exception("can only use return inside function\n" + self.reporter.mark(node))
        node.expr and node.expr.accept(self)
        node.scope = self.scope_manager.current_scope

    def visit_identifier(self, node: 'IdNode'):
        node.scope = self.scope_manager.current_scope

    def visit_type_init(self, node: 'StructInitNode'):
        node.scope = self.scope_manager.current_scope
        node.type_name.accept(self)
        for body in node.body:
            body.accept(self)

    def visit_function_type(self, node: 'FunctionTypeNode'):
        node.scope = self.scope_manager.current_scope
        for arg_type in node.args:
            arg_type.accept(self)
        node.return_type and node.return_type.accept(self)

    def visit_trait_def(self, node: 'TraitDefNode'):
        node.scope = self.scope_manager.current_scope
        trait = TraitSymbol(node.name_and_param.name, node.type_var.string)
        self.add_symbol(trait, node)
        with self.scope_manager.new_scope() as scope:
            scope.add_type_var(TypeSymbol(node.type_var.string))
            for f in node.functions:
                f.accept(self)
                trait.add_function(f.name.string, utils.extract_type_from_ast(f))

    def visit_trait_function(self, node: 'TraitFunctionNode'):
        node.scope = self.scope_manager.current_scope
        func = FunctionSymbol(node.name.string, utils.extract_type_from_ast(node), func_def=node, belong_to_trait=True)
        self.scope_manager.add_var(func)
        with self.scope_manager.new_scope():
            for arg in node.args:
                arg.accept(self)
            node.return_type.accept(self)

    def visit_trait_impl(self, node: 'TraitImplNode'):
        node.scope = self.scope_manager.current_scope
        node.target_type.accept(self)
        with self.scope_manager.new_scope() as scope:
            for function in node.functions:
                function.accept(self)

    def visit_attribute(self, node: 'AttributeNode'):
        node.scope = self.scope_manager.current_scope
        node.data.accept(self)
        node.attr.accept(self)

    def visit_type_constraint(self, node: 'TraitConstraintNode'):
        node.scope = self.scope_manager.current_scope
        for trait in node.traits:
            trait.accept(self)

    def visit_trait_node(self, node: 'TraitNode'):
        node.scope = self.scope_manager.current_scope

    def visit_continue_or_break(self, node: 'ContinueOrBreak'):
        if not self.inside_loop:
            raise SyntaxError(f"can only use {node.kind} inside function\n" + self.reporter.mark(node))

    def visit_type_annotation(self, node: 'TypeAnnotation'):
        node.scope = self.scope_manager.current_scope
        self.add_symbol(TypeSymbol(node.name, utils.extract_type_from_ast(node)), node)

    def visit_type_var(self, node: 'TypeVarNode'):
        self.add_symbol(TypeSymbol(node.name.string, utils.extract_type_from_ast(node), is_var=True), node)

class SymbolDefinitionVisitor(Visitor):

    def __init__(self, error_reporter: ErrorReporter):
        self.error_reporter = error_reporter

    def visit_bin_op(self, node: 'BinaryOpNode'):
        node.left.accept(self)
        node.right.accept(self)

    def visit_assign(self, node: 'AssignNode'):
        node.var.accept(self)
        node.assign_expr.accept(self)

    def visit_lit(self, node: 'LiteralNode'):
        return None

    def visit_var(self, node: 'VarNode'):
        node.identifier.accept(self)

    def visit_block(self, node: 'BlockNode'):
        for stmt in node.stmts:
            stmt.accept(self)

    def visit_function_call(self, node: 'FunctionCallNode'):
        node.call_source.accept(self)

    def visit_if(self, node: 'IfStatement'):
        for condition, statement in node.branches:
            condition.accept(self)
            statement.accept(self)
        node.else_branch and node.else_branch.accept(self)

    def visit_loop(self, node: 'LoopStatement'):
        node.condition.accept(self)
        node.body.accept(self)

    def visit_function_def(self, node: 'FunctionDefNode'):
        for arg in node.args:
            arg.accept(self)
        if node.trait_node:
            node.scope.add_var(TBDSymbol("self"))
        node.body.accept(self)
        node.return_type.accept(self)

    def visit_proc(self, node: 'ProcNode'):
        for stmt in node.children:
            stmt.accept(self)

    def visit_var_def(self, node: 'VarDefNode'):
        node.var_type and node.var_type.accept(self)
        node.init_expr and node.init_expr.accept(self)

    def visit_type(self, node: 'StructNode'):
        if not node.scope.lookup_struct(node.name):
            self.error_reporter.add_undefined_error_by_ast(node.name, node)
            return False
        return True

    def visit_type_def(self, node: 'StructDefNode'):
        for _, d in node.fields:
            d.accept(self)

    def visit_return(self, node: 'ReturnNode'):
        node.expr.accept(self)

    def visit_identifier(self, node: 'IdNode'):
        if not node.scope.lookup(node.string):
            self.error_reporter.add_undefined_error_by_ast(node.string, node)

    def visit_type_init(self, node: 'StructInitNode'):
        structure_type = node.scope.lookup_struct(node.type_name.name)
        if not structure_type:
            self.error_reporter.report_undefined("", node.type_name.name, node.type_name)
        structure_type = node.scope.lookup_struct(node.type_name.name)
        for assign in node.body:
            if assign.var.identifier.string not in structure_type.fields.types:
                self.error_reporter.add_undefined_message(f"unresolved attribute '{assign.var.identifier.string}' for type '{node.type_name.name}'", assign)
            assign.assign_expr.accept(self)

    def visit_function_type(self, node: 'FunctionTypeNode'):
        for n in node.args:
            n.accept(self)
        node.return_type.accept(self)

    def visit_trait_function(self, node: 'TraitFunctionNode'):
        for arg in node.args:
            arg.accept(self)
        node.return_type.accept(self)

    def visit_trait_def(self, node: 'TraitDefNode'):
        for func in node.functions:
            func.accept(self)

    def visit_trait_impl(self, node: 'TraitImplNode'):
        node.target_type.accept(self)
        for node in node.functions:
            node.accept(self)

    def visit_trait_node(self, node: 'TraitNode'):
        if not node.scope.lookup_traits(node.name.string):
            self.error_reporter.add_undefined_error_by_ast(node.name.string, node)

    def visit_type_constraint(self, node: 'TraitConstraintNode'):
        for trait in node.traits:
            trait.accept(self)

    def visit_attribute(self, node: 'AttributeNode'):
        node.data.accept(self)




class ReferenceResolveVisitor(Visitor):

    def __init__(self, error_reporter: ErrorReporter):
        self.error_reporter = error_reporter
        self.expect_return_type = None

    def visit_type_def(self, node: 'StructDefNode') -> BaseType:
        type_def = utils.extract_type_from_ast(node, {param.name.string for param in node.name_and_param.parameters})
        type_symbol = node.scope.lookup_struct(node.name_and_param.name)
        assert type_symbol
        type_symbol.fields = type_def
        return type_def

    def visit_bin_op(self, node: 'BinaryOpNode') -> BaseType:
        left_type = node.left.accept(self)
        right_type = node.right.accept(self)
        if node.op in ('+', '-', '*', '/'):
            if left_type != right_type:
                if VarType.Float.name in (left_type, right_type):
                    return Type(VarType.Float.name)
                else:
                    pass # todo: add exception
                    #raise TypeError(f"type mismatch between {left_type} and {right_type}\n" + self.line_marker.mark(node.left.start_pos, node.right.end_pos))
            else:
                return left_type
        if node.op in ('>', "<", '==', '>=', '<=', '!='):
            return Type(VarType.Bool.name)
        return left_type

    def visit_assign(self, node: 'AssignNode'):
        return None

    def visit_lit(self, node: 'LiteralNode') -> BaseType:
        return Type(node.literal_type)

    def visit_var(self, node: 'VarNode') -> BaseType:
        defined_var = node.scope.lookup(node.identifier.string)
        if isinstance(defined_var, VarSymbol):
            return defined_var.var_type
        elif isinstance(defined_var, FunctionSymbol):
            return defined_var.signature
        utils.died_branch()

    def visit_block(self, node: 'BlockNode'):
        return_type = self.expect_return_type
        has_return_node = False
        for stmt in node.stmts:
            stmt.accept(self)
            if isinstance(stmt, ReturnNode):
                if self.expect_return_type == UNIT:
                    raise TypeError(f"cannot return a value from a method with unit result type\n" + self.error_reporter.mark(stmt, context_node=node))
                has_return_node = True
                detect_return_type = stmt.expr.accept(self)
                type_check_res = utils.type_check(return_type, detect_return_type, node.scope)
                if isinstance(type_check_res, set):
                    raise TypeConstraintError(f"Type constraints check failed. "
                                              f"trait {type_check_res} is not implement in type `{detect_return_type}`.\n" + self.error_reporter.mark(
                        stmt, context_node=node))
                if type_check_res:
                    raise TypeError(
                        f"Expected return type `{return_type}` but got type `{detect_return_type}`.\n" + self.error_reporter.mark(
                            stmt, context_node=node))
        return self.expect_return_type if has_return_node else None

    def visit_function_def(self, node: 'FunctionDefNode'):
        for var_def in node.args:
            var_def.accept(self)
        return_type = node.return_type.accept(self)
        self.expect_return_type = return_type
        if node.trait_node:
            node.scope.replace("self", VarSymbol("self", Type(node.trait_node.target_type.name)))
        node.body.accept(self)
        # for stmt in node.body.stmts:
        #     if isinstance(stmt, ReturnNode):
        #         if return_type == UNIT:
        #             # raise TypeConstraintError(f"Return is not allowed for unit return type.\n"+ self.error_reporter.mark(stmt, context_node=node))
        #             raise TypeError(f"cannot return a value from a method with unit result type\n" + self.error_reporter.mark(stmt, context_node=node))
        #
        #         detect_return_type = stmt.expr.accept(self)
        #         type_check_res = utils.type_check(return_type, detect_return_type, node.scope)
        #         if isinstance(type_check_res, set):
        #             raise TypeConstraintError(f"Type constraints check failed. "
        #                                       f"trait {type_check_res} is not implement in type `{detect_return_type}`.\n" + self.error_reporter.mark(
        #                 stmt, context_node=node))
        #         if type_check_res:
        #             raise TypeError(f"Expected return type `{return_type}` but got type `{detect_return_type}`.\n" + self.error_reporter.mark(stmt, context_node=node))
        #     else:
        #         stmt.accept(self)
        self.expect_return_type = None

    def visit_function_call(self, node: 'FunctionCallNode') -> BaseType:
        call_source_type: FunctionSignature = node.call_source.accept(self)
        node.signature = call_source_type

        node.is_trait_function = call_source_type.is_trait_function
        if not isinstance(call_source_type, FunctionSignature):
            self.error_reporter.report_undefined_message("result of expr is not callable", node.call_source)
        args_type = tuple([x.accept(self) for x in node.args])
        expect_arg_length = len(call_source_type.args)
        actual_arg_length = len(node.args)
        if expect_arg_length != actual_arg_length:
            raise TypeError(f"expect {expect_arg_length} args for function but {actual_arg_length} given \n" + self.error_reporter.mark(node))

        for index, types in enumerate(zip_longest(call_source_type.args, args_type)):
            expect_type, actual_type = types
            type_check_res = utils.type_check(expect_type, actual_type, node.scope)
            if isinstance(expect_type, set):
                    raise TypeConstraintError(f"Type constraints check failed. "
                                              f"trait '{type_check_res}' is not implemented in type '{actual_type}'.\n"+self.error_reporter.mark(node.args[index], context_node=node))
            elif type_check_res is True:
                raise TypeError(f"expected type '{expect_type}' but got type '{actual_type}'.\n" + self.error_reporter.mark(node.args[index], context_node=node))
        return call_source_type.return_type

    def visit_if(self, node: 'IfStatement'):
        for branch, body in node.branches:
            if (condition_type := branch.accept(self)) != Type(VarType.Bool.value):
                raise TypeError(f"expect type 'Bool', but got '{condition_type}'\n" + self.error_reporter.mark(branch))
            if self.expect_return_type and not body.accept(self):
                raise UndefinedError("missing return statement in branch\n" + self.error_reporter.mark(branch, context_node=node))
        if node.else_branch:
            if self.expect_return_type and not node.else_branch.accept(self):
                raise UndefinedError("missing return statement in branch\n" + self.error_reporter.mark(node.else_branch, context_node=node))

    def visit_loop(self, node: 'LoopStatement'):
        pass


    def visit_proc(self, node: 'ProcNode'):
        for child in node.children:
            child.accept(self)

    def visit_type(self, node: 'StructNode'):
        return Type(node.name)

    def visit_var_def(self, node: 'VarDefNode'):
        # 判断变量是否指定类型
        decl_type = node.var_type and node.var_type.accept(self)
        # 根据初始化表达式推断类型
        init_type = node.init_expr and node.init_expr.accept(self)

        # 如果类型不兼容
        if decl_type and init_type and decl_type != init_type:
            raise TypeError(f"Expect type '{decl_type}', but got '{init_type}'.\n" + self.error_reporter.mark(node.init_expr))
        final_type = decl_type or init_type

        if type(final_type) is FunctionSignature:
            node.scope.replace(node.var_node.string, FunctionSymbol(node.var_node.string, final_type))
        else:
            node.scope.replace(node.var_node.string, VarSymbol(node.var_node.string, final_type))
        return final_type


    def visit_return(self, node: 'ReturnNode'):
        return node.expr.accept(self)

    def visit_identifier(self, node: 'IdNode'):
        pass

    def visit_type_init(self, node: 'StructInitNode'):
        data_type = node.scope.lookup_struct(node.type_name.name)
        res = {}
        type_infers = {}
        for expr in node.body:
            name = expr.var.identifier.string
            impl_type = expr.assign_expr.accept(self)
            defined_type = data_type.fields.types.get(name)
            assert defined_type is not None
            if isinstance(defined_type, TypeVar):
                type_var_name = defined_type.name
                inferred_type = type_infers.get(type_var_name)
                if inferred_type and inferred_type != defined_type:
                    raise TypeError(f"{defined_type} is not match with {impl_type}")
                elif inferred_type is None:
                    type_infers[type_var_name] = impl_type
            elif impl_type != defined_type:
                raise TypeError(f"{defined_type} is not match with {impl_type}")
            res[name] = impl_type
        return Type(node.type_name.name)

    def visit_function_type(self, node: 'FunctionTypeNode'):
        for arg_type in node.args:
            if not node.scope.lookup_struct(arg_type.name):
                self.error_reporter.report_undefined("Type", arg_type.name, arg_type)
        if not node.scope.lookup_struct(node.return_type.name):
            self.error_reporter.report_undefined("Type", node.return_type.name, node.return_type)
        return utils.extract_type_from_ast(node)

    def visit_trait_function(self, node: 'TraitFunctionNode'):
        super().visit_trait_function(node)

    def visit_trait_def(self, node: 'TraitDefNode'):
        super().visit_trait_def(node)

    def visit_trait_impl(self, node: 'TraitImplNode'):
        trait_symbol = node.scope.lookup_traits(node.trait.name.string)
        impled_functions = {f.name.string: f for f in node.functions}
        for impl_func_name, signature in trait_symbol.functions.items():
            defined_signature = signature.replace_type_var(trait_symbol.type_var_name, node.target_type.name)
            if not impled_functions.get(impl_func_name):
                raise ValueError(f"Function {impl_func_name} is not implemented")
            impl_signature = utils.extract_type_from_ast(impled_functions.get(impl_func_name))
            if impl_signature is None:
                raise ValueError(f"Trait function {impl_func_name} is not implemented")
            if impl_signature != defined_signature:
                raise ValueError(f"Function signature {impl_signature} is not match in trait {defined_signature}")
            node.scope.impl_trait(node.target_type.name, trait_symbol.name, FunctionSymbol(impl_func_name, impl_signature))
        for f in node.functions:
            f.accept(self)

    def visit_trait_node(self, node: 'TraitNode'):
        super().visit_trait_node(node)

    def visit_attribute(self, node: 'AttributeNode'):
        t = node.data.accept(self)
        if isinstance(t, TraitConstraintsType):
            for trait_name in t.constraints:
                trait_symbol = node.scope.lookup_traits(trait_name)
                if node.attr.string in trait_symbol.functions:
                    return trait_symbol.functions[node.attr.string]
            raise ValueError(f"attr {node.attr.string} not found in {t}")
        else:
            resolved_type = node.scope.lookup_struct(t.string).fields
            # 先寻找类型中定义的 attribute
            if node.attr.string not in resolved_type.types:
                resolved_trait_func = None
                impled_trait = node.scope.get_impl_by_target(t.string)
                # 没有的话去实现的 trait 中找
                for trait, function_symbols in impled_trait.items():
                    for function_symbol in function_symbols:
                        if function_symbol.string == node.attr.string: # todo: raise exception if there are multiple impls with same function name
                            resolved_trait_func = function_symbol.signature
                            break
                if not resolved_trait_func:
                    raise ValueError(f"attr {node.attr.string} not found in {t.string}")
                return resolved_trait_func
        return resolved_type.types[node.attr.string]

    def visit_type_constraint(self, node: 'TraitConstraintNode'):
        return TraitConstraintsType([x.name.string for x in node.traits])

class EvalVisitor(Visitor):
    def __init__(self, global_scope: Scope, meta_manager: MetaManager, code_generator: PythonCodeGenerator):
        self.stacks = Stack(global_scope)
        self.meta_manager = meta_manager
        self.code_gen = code_generator

    def visit_bin_op(self, node: 'BinaryOpNode'):
        left = node.left.accept(self)
        right = node.right.accept(self)
        return f"{left} {node.op} {right}"

    def visit_assign(self, node: 'AssignNode'):
        return f"{node.var.identifier.string}={node.assign_expr.accept(self)}"

    def visit_lit(self, node: 'LiteralNode'):
        match VarType(node.literal_type):
            case VarType.Float: return float(node.val)
            case VarType.Int: return int(node.val)
            case VarType.Bool: return bool(node.val)
            case VarType.String: return node.val
            case _: return node.val

    def visit_var(self, node: 'VarNode'):
        return node.identifier.string

    def visit_block(self, node: 'BlockNode'):
        res = "\n".join([utils.indent(stmt.accept(self), 1)   for stmt in node.stmts] )
        return res

    def visit_function_call(self, node: 'FunctionCallNode'):
        function_call_source = node.call_source.accept(self)
        arg_str = ",".join([var.accept(self) for var in node.args])
        if isinstance(node.call_source, AttributeNode) and node.is_trait_function:
            data = node.call_source.data.accept(self)
            arg_str = f"{data},{arg_str}"
        return f"{function_call_source}({arg_str})"



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
        function_name = f"__{node.trait_node.trait.name.string}__{node.trait_node.target_type.name}__{node.name.string}" if node.trait_node else node.name.string
        args = [x.var_node.string for x in node.args]
        node.trait_node and args.insert(0, "self")
        res = [
                f"def {function_name}({','.join(args)}):",
                node.body.accept(self)
            ]
        return "\n".join(res)


    def visit_proc(self, node: 'ProcNode'):
        res = []
        for x in node.children:
            code = x.accept(self)
            if code:
                res.append(code)
        return "\n".join(res)

    def visit_var_def(self, node: 'VarDefNode'):
        return f"{node.var_node.string} = {node.init_expr.accept(self)}"

    def visit_type(self, node: 'StructNode'):
        pass

    def visit_type_def(self, node: 'StructDefNode'):
        self.meta_manager.add_meta(DataMeta(node.type_name.string))

    def visit_return(self, node: 'ReturnNode'):
        return f"return {node.expr.accept(self)}"

    def visit_identifier(self, node: 'IdNode'):
        pass

    def visit_type_init(self, node: 'StructInitNode'):
        data_code = "{" + ", ".join([f"'{x.var.identifier.string}':{x.assign_expr.accept(self)}" for x in node.body]) + "}"
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
        res = []
        for function in node.functions:
            function_name = function.name.string
            compile_name = f"__{node.trait.name.string}__{node.target_type.name}__{function_name}"
            res.append(function.accept(self))
            res.append(f"meta_manager.get_meta('{target_type_name}').vtable['{function_name}'] = {compile_name}")
        return "\n".join(res)


    def visit_trait_node(self, node: 'TraitNode'):
        super().visit_trait_node(node)

    def visit_type_constraint(self, node: 'TraitConstraintNode'):
        super().visit_type_constraint(node)









