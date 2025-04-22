import json
from typing import List, Any, Tuple, Optional
from abc import ABC, abstractmethod
from parser.scope import SCOPE_MANAGER
from parser.visitor import Visitor

class ASTNode(ABC):

    def __init__(self, node_type):
        self.node_type = node_type

    @abstractmethod
    def eval(self) -> Any: pass

    def __str__(self):

        def helper(data, level=0):
            if type(data) is dict:
                r = {}
                for k, v in data.items():
                    if isinstance(v, list) or isinstance(v, tuple):
                        r[k] = helper(v, level + 1)
                    elif isinstance(v, ASTNode):
                        r[k] = helper(v, level + 1)
                    else:
                        r[k] = v
                return r
            elif type(data) is list:
                return [helper(x, level + 1) for x in data]
            elif type(data) is tuple:
                return [helper(x, level + 1) for x in data]
            elif isinstance(data, ASTNode):
                return helper(data.__dict__, level + 1)
            return str(data)

        res = helper(self)
        print(res)
        return json.dumps(res, indent=4)

    @abstractmethod
    def visit(self, visitor: Visitor): pass


    def __repr__(self):
        return self.__str__()


class BinaryOpNode(ASTNode):

    def __init__(self, op, left: ASTNode=None, right: ASTNode=None):
        super().__init__("bin_op")
        self.op = op
        self.left = left
        self.right = right

    def eval(self) -> Any:
        return eval(f"{self.left.eval()} {self.op} {self.right.eval()}")

    def visit(self, visitor: Visitor):
        return visitor.visit_bin_op(self)


class AssignNode(ASTNode):

    def __init__(self, left: ASTNode=None, right: ASTNode=None):
        super().__init__("assign_op")
        self.left = left
        self.right = right

    def eval(self) -> Any:
        key = self.left.name
        value = self.right.eval()
        SCOPE_MANAGER.current.set(key, value)
        return value

    def visit(self, visitor: Visitor):
        return visitor.visit_assign(self)

class LiteralNode(ASTNode):

    def __init__(self, val):
        super().__init__("lit")
        self.val = val

    def eval(self) -> Any:
        if self.node_type == "int":
            return int(self.val)
        if self.node_type == "float":
            return float(self.val)
        if self.node_type == "lit":
            return self.val
        return self.val

    def visit(self, visitor: Visitor):
        return visitor.visit_lit(self)


class VarNode(ASTNode):

    def __init__(self, name):
        super().__init__("var")
        self.name = name

    def eval(self) -> Any:
        return SCOPE_MANAGER.current.lookup(self.name)

    def visit(self, visitor: Visitor):
        return visitor.visit_var(self)


class BlockNode(ASTNode):

    def __init__(self, stmts: List[ASTNode]):
        super().__init__("stmt")
        self.stmts = stmts

    def eval(self) -> Any:
        res = None
        for child in self.stmts:
           res = child.eval()
        return res


    def visit(self, visitor: Visitor):
        return visitor.visit_block(self)

class FunctionCallNode(ASTNode):

    def __init__(self, function_name):
        super().__init__("func_call")
        self.function_name = function_name
        self.args: List[ASTNode] = []

    def eval(self) -> Any:
        func = SCOPE_MANAGER.current_scope.lookup(self.function_name)
        SCOPE_MANAGER.enter()
        if isinstance(func, FuncDefStatement):
            arg_names = func.args
            for name, value in zip(arg_names, self.args):
                SCOPE_MANAGER.current_scope.set(name, value.eval())
            res = func.body.eval()
        else:
            res = func(*[x.eval() for x in self.args])
        SCOPE_MANAGER.exit()
        return res

    def visit(self, visitor: Visitor):
        return visitor.visit_function_call(self)



class IndexNode(ASTNode):

    def __init__(self, target_node: ASTNode, index_node: ASTNode):
        super().__init__("index")
        self.target_node = target_node
        self.index_node = index_node

    def eval(self) -> Any:
        return None

    def __str__(self):
        return f"{self.target_node}[{self.index_node}]"

    def __expr__(self):
        return self.__str__()


class LitArrayNode(ASTNode):

    def __init__(self, args: List[ASTNode]):
        super().__init__("lit_array")
        self.args = args

    def eval(self) -> Any:
        return list((x.eval() for x in self.args))



class LitDictNode(ASTNode):

    def __init__(self, args: List[Tuple[ASTNode, ASTNode]]):
        super().__init__("lit_array")
        self.args = args

    def eval(self) -> Any:
        return dict(((x.eval(), y.eval()) for x, y in self.args))


class IfStatement(ASTNode):

    def __init__(self, branches: List[Tuple[ASTNode, ASTNode]], else_branch: Optional[BlockNode]):
        super().__init__("if_stmt")
        self.branches = branches
        self.else_branch = else_branch

    def eval(self) -> Any:
        for condition, body in self.branches:
            if condition.eval():
                return body.eval()
        if self.else_branch:
            return self.else_branch.eval()

    def visit(self, visitor: Visitor):
        return visitor.visit_if(self)

class LoopStatement(ASTNode):
    def __init__(self, condition: ASTNode, body: ASTNode):
        super().__init__("loop_stmt")
        self.condition = condition
        self.body = body

    def eval(self) -> Any:
        while self.condition.eval():
            self.body.eval()


class FuncDefStatement(ASTNode):

    def __init__(self, name: str, args: List[ASTNode], body: BlockNode):
        super().__init__("func_def")
        self.name = name
        self.args = args
        self.body = body

    def eval(self) -> Any:
        SCOPE_MANAGER.current_scope.set(self.name, self)


    def visit(self, visitor: Visitor):
        return visitor.visit_funcdef(self)

class ProcNode(ASTNode):

    def __init__(self):
        super().__init__("proc")
        self.children: List[ASTNode] = []

    def eval(self) -> Any:
        for child in self.children:
            child.eval()

    def visit(self, visitor: Visitor):
        return visitor.visit_proc(self)