import json
from typing import List, Any, Tuple, Optional
from abc import ABC, abstractmethod
from parser.scope import SCOPE_MANAGER, Scope


class ASTNode(ABC):

    def __init__(self, node_type: str):
        self.node_type = node_type
        self.scope: Optional[Scope] = None

    @abstractmethod
    def eval(self) -> Any: pass

    @abstractmethod
    def accept(self, visitor: 'Visitor'): pass

    def walk(self):
        def helper(data, level=0):
            if type(data) is dict:
                r = {}
                for k, v in data.items():
                    if k in ("scope", "node_type"):
                        continue
                    if isinstance(v, list) or isinstance(v, tuple):
                        r[k] = helper(v, level + 1)
                    elif isinstance(v, ASTNode):
                        r[k] = helper(v, level + 1)
                    elif isinstance(v, dict):
                        r[k] = helper(v, level + 1)
                    else:
                        r[k] = v
                return r
            elif type(data) in (list, tuple):
                return [helper(x, level + 1) for x in data]
            elif isinstance(data, ASTNode):
                return {"_class": data.__class__.__name__} | helper(data.__dict__, level + 1)
            return str(data)

        res = helper(self)

        def pretty(data, level=0):
            if type(data) is dict:
                if "_class" in data:
                    class_name = data["_class"]
                    data.pop("_class")
                    plain_kv = [str(k) + ":" + str(v) for k, v in data.items() if type(v) not in (list, tuple, dict)]
                    postfix = f'({",".join(plain_kv)})' if plain_kv else ""
                    print(' ' * level + class_name + postfix)
                    level += 1
                    # if len(data) == 1:
                    #     key = list(data.keys())[0]
                    #     value = data[key]
                    #     print(' ' * level + key, end='->')
                    #     pretty(value, 0)
                    for k, v in data.items():
                        if isinstance(v, list) or isinstance(v, tuple):
                            print(' ' * level + k)
                            for i in v:
                                pretty(i, level + 1)
                        if isinstance(v, dict):
                            print(' ' * level + k)
                            pretty(v, level + 1)
            elif type(data) in (list, tuple):
                for i in data:
                    pretty(i, level + 1)
            else:
                print(' '* level, data)
        pretty(res, 0)




class Nothing(ASTNode):
    def eval(self) -> Any:
        return None
    def accept(self, visitor: 'Visitor'):
        return None


class BinaryOpNode(ASTNode):

    def __init__(self, op, left: ASTNode=None, right: ASTNode=None):
        super().__init__("bin_op")
        self.op = op
        self.left = left
        self.right = right

    def eval(self) -> Any:
        return eval(f"{self.left.eval()} {self.op} {self.right.eval()}")

    def accept(self, visitor: 'Visitor'):
        return visitor.visit_bin_op(self)



class IdNode(ASTNode):

    def __init__(self, name):
        super().__init__("id")
        self.name = name

    def eval(self) -> Any:
        return SCOPE_MANAGER.current.lookup(self.name)

    def accept(self, visitor: 'Visitor'):
        return None


class VarNode(ASTNode):
    def __init__(self, name: IdNode):
        super().__init__("var")
        self.name = name

    def eval(self) -> Any:
        return SCOPE_MANAGER.current.lookup(self.name)

    def accept(self, visitor: 'Visitor'):
        return visitor.visit_var(self)

class AssignNode(ASTNode):

    def __init__(self, left: VarNode=None, right: ASTNode=None):
        super().__init__("assign_op")
        self.left = left
        self.right = right

    def eval(self) -> Any:
        key = self.left.name
        value = self.right.eval()
        SCOPE_MANAGER.current.set(key, value)
        return value

    def accept(self, visitor: 'Visitor'):
        return visitor.visit_assign(self)

class LiteralNode(ASTNode):

    def __init__(self, val, literal_type: str):
        super().__init__("lit")
        self.val = val
        self.literal_type = literal_type

    def eval(self) -> Any:
        if self.literal_type == "int":
            return int(self.val)
        if self.literal_type == "float":
            return float(self.val)
        if self.literal_type == "string":
            return self.val
        return self.val

    def accept(self, visitor: 'Visitor'):
        return visitor.visit_lit(self)



class TypeNode(ASTNode):

    def __init__(self, name):
        super().__init__("type")
        self.name = name

    def eval(self) -> Any:
        return None

    def accept(self, visitor: 'Visitor'):
        return visitor.visit_type(self)


class BlockNode(ASTNode):

    def __init__(self, stmts: List[ASTNode]):
        super().__init__("stmt")
        self.stmts = stmts

    def eval(self) -> Any:
        res = None
        for child in self.stmts:
           res = child.eval()
        return res


    def accept(self, visitor: 'Visitor'):
        return visitor.visit_block(self)

class FunctionCallNode(ASTNode):

    def __init__(self, function_name, args=None):
        super().__init__("func_call")
        self.function_name = function_name
        self.args: List[ASTNode] = args or []
        self.define: 'FuncDefNode' = None
        self.symbol: 'FunctionSymbol' = None

    def eval(self) -> Any:
        func = SCOPE_MANAGER.current_scope.lookup(self.function_name)
        SCOPE_MANAGER.enter()
        if isinstance(func, FuncDefNode):
            arg_names = func.args
            for name, value in zip(arg_names, self.args):
                SCOPE_MANAGER.current_scope.set(name, value.eval())
            res = func.body.eval()
        else:
            res = func(*[x.eval() for x in self.args])
        SCOPE_MANAGER.exit()
        return res

    def accept(self, visitor: 'Visitor'):
        return visitor.visit_function_call(self)



class IndexNode(ASTNode):

    def __init__(self, target_node: VarNode, index_node: ASTNode):
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

    def __init__(self, branches: List[Tuple[ASTNode, BlockNode]], else_branch: Optional[BlockNode]):
        super().__init__("if_stmt")
        self.branches = branches
        self.else_branch = else_branch

    def eval(self) -> Any:
        for condition, body in self.branches:
            if condition.eval():
                return body.eval()
        if self.else_branch:
            return self.else_branch.eval()

    def accept(self, visitor: 'Visitor'):
        return visitor.visit_if(self)

class LoopStatement(ASTNode):
    def __init__(self, condition: ASTNode, body: ASTNode):
        super().__init__("loop_stmt")
        self.condition = condition
        self.body = body

    def eval(self) -> Any:
        while self.condition.eval():
            self.body.eval()

class TypeDefNode(ASTNode):
    def __init__(self, type_name: IdNode, type_def: List[Tuple[IdNode, TypeNode]]):
        super().__init__("type_def")
        self.type_name = type_name
        self.type_def = type_def

    def eval(self) -> Any:
        return None
    def accept(self, visitor: 'Visitor'):
        visitor.visit_type_def(self)


class VarDefNode(ASTNode):
    def __init__(self, var_node: IdNode, var_type: TypeNode, init_expr: ASTNode=None):
        super().__init__("var_decl")
        self.var_node = var_node
        self.var_type = var_type
        self.init_expr = init_expr

    def eval(self) -> Any:
        return None

    def accept(self, visitor: 'Visitor'):
        visitor.visit_var_def(self)



class FuncDefNode(ASTNode):

    def __init__(self, name: IdNode, args: List[VarDefNode], body: BlockNode, return_type: TypeNode):
        super().__init__("func_def")
        self.name = name
        self.args = args
        self.body = body
        self.return_type = return_type

    def eval(self) -> Any:
        SCOPE_MANAGER.current_scope.add(self.name, self)


    def accept(self, visitor: 'Visitor'):
        return visitor.visit_funcdef(self)

class ProcNode(ASTNode):

    def __init__(self):
        super().__init__("proc")
        self.children: List[ASTNode] = []

    def eval(self) -> Any:
        for child in self.children:
            child.eval()

    def accept(self, visitor: 'Visitor'):
        return visitor.visit_proc(self)

class ReturnNode(ASTNode):

    def __init__(self, expr: ASTNode=None):
        super().__init__("return")
        self.expr = expr

    def eval(self) -> Any:
        pass

    def accept(self, visitor: 'Visitor'):
        return visitor.visit_return(self)

