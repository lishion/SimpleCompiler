from parser.stack import StackFrame, Stack
from parser.symbol import VarSymbol, TypeSymbol, FunctionSymbol
from parser.node import *
from abc import ABC, abstractmethod
from parser.types import VarType


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
    def visit_funcdef(self, node: 'FuncDefNode'):
        return None

    @abstractmethod
    def visit_proc(self, node: 'ProcNode'):
        return None

    @abstractmethod
    def visit_var_def(self, node: 'VarDefNode'):
        return None

    @abstractmethod
    def visit_type(self, node: 'TypeNode'):
        return None

    @abstractmethod
    def visit_type_def(self, node: 'TypeNode'):
        return None

    def visit_return(self, node: 'ReturnNode'):
        return None


# class PrintVisitor(Visitor, ABC):
#
#     def visit_bin_op(self, node: 'BinaryOpNode'):
#         print(node.__class__.__name__)
#         print(node.left.visit(self))
#         print(node.right.visit(self))
#
#     def visit_assign(self, node: 'AssignNode'):
#         print(node.__class__.__name__)
#         print(node.left.visit(self))
#         print(node.right.visit(self))
#
#     def visit_lit(self, node: 'LiteralNode'):
#         print(node.__class__.__name__)
#         print(node.val)
#
#     def visit_var(self, node: 'VarNode'):
#         print(node.__class__.__name__)
#         print(node.name)
#
#     def visit_block(self, node: 'BlockNode'):
#         print(node.__class__.__name__)
#         for stmt in node.stmts:
#             print(stmt.visit(this))
#
#     def visit_function_call(self, node: 'FunctionCallNode'):
#         print(node.__class__.__name__)
#         print(node.function_name)
#
#     def visit_if(self, node: 'IfStatement'):
#         print(node.__class__.__name__)
#         print(node.branches)
#
#     def visit_loop(self, node: 'LoopStatement'):
#         print(node.__class__.__name__)
#         print(node.body)
#
#     def visit_funcdef(self, node: 'FuncDefStatement'):
#         print(node.__class__.__name__)
#         print(node.args)
#
#     def visit_proc(self, node: 'ProcNode'):
#         print(node.__class__.__name__)
#         for child in node.children:
#             print(child.visit(self))
#
#     def visit_var_def(self, node: 'VarDeclNode'):


class SymbolVisitor(Visitor):
    
    def __init__(self, scope_manager: 'ScopeManager'):
        self.scope_manager = scope_manager

    def visit_bin_op(self, node: 'BinaryOpNode'):
        node.left.accept(self)
        node.right.accept(self)

    def visit_assign(self, node: 'AssignNode'):
        node.scope = self.scope_manager.current_scope

    def visit_lit(self, node: 'LiteralNode'):
        pass

    def visit_var(self, node: 'VarNode'):
        node.scope = self.scope_manager.current_scope

    def visit_var_def(self, node: 'VarDefNode'):
        symbol = VarSymbol(node.var_node.name, node.var_type and node.var_type.name, node.init_expr)
        self.scope_manager.add(symbol)
        node.scope = self.scope_manager.current_scope
        node.var_node.accept(self)
        node.init_expr and node.init_expr.accept(self)

    def visit_block(self, node: 'BlockNode'):
        node.scope = self.scope_manager.current_scope
        with self.scope_manager.new_scope():
            for stmt in node.stmts:
                stmt.accept(self)


    def visit_function_call(self, node: 'FunctionCallNode'):
        node.scope = self.scope_manager.current_scope
        for arg in node.args:
            arg.accept(self)

    def visit_if(self, node: 'IfStatement'):
        for condition, body in node.branches:
            body.accept(self)
        if node.else_branch:
            node.else_branch.accept(self)

    def visit_loop(self, node: 'LoopStatement'):
        node.scope = self.scope_manager.current_scope
        with self.scope_manager.new_scope() as scope:
            node.body.accept(self)


    def visit_funcdef(self, node: 'FuncDefNode'):
        node.scope = self.scope_manager.current_scope
        func = FunctionSymbol(node.name.name, tuple(x.var_type.name for x in node.args), node.return_type, func_def=node)
        self.scope_manager.add(func)
        with self.scope_manager.new_scope():
            for arg in node.args:
                arg.accept(self)
            node.body.accept(self)


    def visit_proc(self, node: 'ProcNode'):
        for child in node.children:
            child.accept(self)

    def visit_type(self, node: 'TypeNode'):
        node.scope = self.scope_manager.current_scope

    def visit_type_def(self, node: 'TypeDefNode'):
        symbol = TypeSymbol(node.type_name.name, type_def=node)
        self.scope_manager.ensure_not_exists(symbol)
        self.scope_manager.current_scope.add(symbol)
        node.scope = self.scope_manager.current_scope
        # for _, type_node in node.type_def:
        #     if not self.scope_manager.current_scope.look(TypeSymbol(type_node.name)):
        #         raise ValueError(f"Type {type_node.name} is not defined")

    def visit_return(self, node: 'ReturnNode'):
        node.expr and node.expr.accept(self)
        node.scope = self.scope_manager.current_scope


class ReferenceResolveVisitor(Visitor):

    def visit_type_def(self, node: 'TypeDefNode') -> str:
        # 判断定义类型时所用到的类型是否已经存在
        for _, type_node in node.type_def:
            if not node.scope.lookup(type_node.name):
                raise ValueError(f"Type {type_node.name} is not defined")
        return node.type_name.name

    def visit_bin_op(self, node: 'BinaryOpNode') -> str:
        left_type = node.left.accept(self)
        right_type = node.right.accept(self)
        if node.op in ('+', '-', '*', '/'):
            if left_type != right_type:
                if VarType.Float.name in (left_type, right_type):
                    return VarType.Float.name
                else:
                    raise ValueError(f"type mismatch between {left_type} and {right_type}")
            else:
                return left_type
        if node.op in ('>', "<", '==', '>=', '<=', '!='):
            return VarType.Bool.name
        return left_type

    def visit_assign(self, node: 'AssignNode'):
        decl = node.scope.lookup(node.left.name.name)
        if not decl:
            raise ValueError(f"Try to assign to an undefined variable {node.left.name.name}")

    def visit_lit(self, node: 'LiteralNode') -> str:
        return node.literal_type

    def visit_var(self, node: 'VarNode'):
        if decl_var := node.scope.lookup(node.name):
            return decl_var.type_name
        raise ValueError(f"Variable {node.name} is not defined")

    def visit_block(self, node: 'BlockNode'):
        for stmt in node.stmts:
            if type(stmt) in (VarDefNode, TypeDefNode, FuncDefNode, IfStatement, LoopStatement):
                stmt.accept(self)
        return None

    def visit_function_call(self, node: 'FunctionCallNode'):
        functions: List[FunctionSymbol] = node.scope.lookup(node.function_name)
        function_type = tuple(x.accept(self) for x in node.args)
        matched_function = None
        for function in functions:
            if function.args_type == function_type:
                matched_function = function
                break
        if not matched_function:
            raise ValueError(f'function {node.function_name} with parameter type ({",".join(function_type)}) is undefined')
        node.define = matched_function.func_def
        node.symbol = matched_function
        return matched_function.return_type and matched_function.return_type.name

    def visit_if(self, node: 'IfStatement'):
        pass

    def visit_loop(self, node: 'LoopStatement'):
        pass

    def visit_funcdef(self, node: 'FuncDefNode'):
        for var_def in node.args:
            if not node.scope.lookup(var_def.var_type.name):
                raise ValueError(f"Type {var_def.var_type.name} is not defined")
        if not node.scope.lookup(node.return_type.name):
            raise ValueError(f"Type {node.return_type.name} is not defined")

        for stmt in node.body.stmts:
            if type(stmt) is ReturnNode:
                detect_return_type = stmt.expr.accept(self)
                if detect_return_type != node.return_type.name:
                    raise ValueError(f"Can not convert return type {detect_return_type} to {node.return_type.name}")
            else:
                stmt.accept(self)
        return node.body.accept(self)

    def visit_proc(self, node: 'ProcNode'):
        for child in node.children:
            child.accept(self)

    def visit_type(self, node: 'TypeNode'):
        return node.name

    def visit_var_def(self, node: 'VarDefNode'):
        var_node = node.var_node
        print(var_node.name)
        # 判断变量是否指定类型
        decl_type = node.var_type and node.var_type.accept(self)
        if decl_type:
            # 如果有指定类型，则需要进一步判断类型是否定义
            type_def = node.scope.lookup(decl_type)
            if not type_def:
                raise ValueError(f"type {decl_type.name} is undefined")
        # 根据初始化表达式推断类型
        init_type = node.init_expr and node.init_expr.accept(self)
        assert init_type is not None # 推断出的类型一定不为空
        # 如果类型不兼容
        if decl_type and init_type and decl_type != init_type:
            raise ValueError(f"Can not convert type from {init_type} to {decl_type}")
        final_type = decl_type or init_type
        node.scope.lookup(var_node.name).type_name = final_type
        print(f"var {var_node.name} is {final_type}")
        return final_type

    def visit_return(self, node: 'ReturnNode'):
        return node.expr.accept(self)


class EvalVisitor(Visitor):
    def __init__(self, global_scope: Scope):
        self.stacks = Stack(global_scope)

    def visit_bin_op(self, node: 'BinaryOpNode'):
        left = node.left.accept(self)
        right = node.right.accept(self)
        return eval(f"{left} {node.op} {right}")

    def visit_assign(self, node: 'AssignNode'):
        self.stacks.current.set(node.left.name.name, node.right.accept(self))

    def visit_lit(self, node: 'LiteralNode'):
        match VarType(node.literal_type):
            case VarType.Float: return float(node.val)
            case VarType.Int: return int(node.val)
            case VarType.Bool: return bool(node.val)
            case VarType.String: return node.val[1:-1]
            case _: return node.val

    def visit_var(self, node: 'VarNode'):
        stack = self.stacks.current
        while stack:
            if node.name in stack.vars:
                res = stack.get(node.name)
                return res
            stack = stack.parent
        raise RuntimeError(f"Variable {node.name} is not defined")

    def visit_block(self, node: 'BlockNode'):
        for stmt in node.stmts:
            res = stmt.accept(self)
            if type(stmt) == ReturnNode:
                return res
        return None

    def visit_function_call(self, node: 'FunctionCallNode'):
        scope = node.scope
        self.stacks.push(StackFrame(scope))
        func_def = node.define
        arg_values = [var.accept(self) for var in node.args]
        if node.symbol.native_call:
            return node.symbol.native_call(*arg_values)
        arg_names = [var.var_node.name for var in func_def.args]
        for name, value in zip(arg_names, arg_values):
            self.stacks.current.set(name, value)
        return_value = func_def.body.accept(self)
        self.stacks.pop()
        return return_value


    def visit_if(self, node: 'IfStatement'):
        pass

    def visit_loop(self, node: 'LoopStatement'):
        pass

    def visit_funcdef(self, node: 'FuncDefNode'):
        pass

    def visit_proc(self, node: 'ProcNode'):
        for stmt in node.children:
            stmt.accept(self)

    def visit_var_def(self, node: 'VarDefNode'):
        self.stacks.current.set(node.var_node.name, node.init_expr and node.init_expr.accept(self))

    def visit_type(self, node: 'TypeNode'):
        pass

    def visit_type_def(self, node: 'TypeNode'):
        pass

    def visit_return(self, node: 'ReturnNode'):
        return node.expr.accept(self)

