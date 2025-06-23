from typing import List, Any, Tuple, Optional, Union
from abc import ABC, abstractmethod
# from parser.scope import Scope
from parser.symbol_type import TraitImpl, TypeRef
from parser.visitor.visitor import Visitor

class ASTNode(ABC):

    def __init__(self):
        self.scope: Optional['Scope'] = None
        self.start_pos = None
        self.end_pos = None

    @abstractmethod
    def accept(self, visitor: 'Visitor'): pass

    def walk(self):
        def helper(data, level=0):
            if type(data) is dict:
                r = {}
                for k, v in data.items():
                    if k in ("scope", "node_type", "start_pos", "end_pos", 'trait_node'):
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
        super().__init__()
        self.op = op
        self.left = left
        self.right = right

    def eval(self) -> Any:
        return eval(f"{self.left.eval()} {self.op} {self.right.eval()}")

    def accept(self, visitor: 'Visitor'):
        return visitor.visit_bin_op(self)

    def __str__(self):
        return f"{self.left} {self.op} {self.right}"

    def __repr__(self):
        return self.__str__()

class IdNode(ASTNode):

    def __init__(self, name):
        super().__init__()
        self.string: str = name


    def accept(self, visitor: 'Visitor'):
        return visitor.visit_identifier(self)


class VarNode(ASTNode):
    def __init__(self, identifier: IdNode, is_self: bool = False):
        super().__init__()
        self.identifier = identifier
        self.is_self = is_self

    def __str__(self):
        return f"{self.identifier.string}"

    def __expr__(self):
        return self.__expr__()

    def accept(self, visitor: 'Visitor'):
        return visitor.visit_var(self)

class AssignNode(ASTNode):

    def __init__(self, var: VarNode=None, right: ASTNode=None):
        super().__init__()
        self.var = var
        self.assign_expr = right

    def accept(self, visitor: 'Visitor'):
        return visitor.visit_assign(self)

class LiteralNode(ASTNode):

    def __init__(self, val, literal_type: str):
        super().__init__()
        self.val = val
        self.literal_type = literal_type


    def accept(self, visitor: 'Visitor'):
        return visitor.visit_lit(self)

    def __str__(self):
        return f"{self.val}"

    def __repr__(self):
        return self.__str__()

class TypeVarNode(ASTNode):

    def __init__(self, identifier: IdNode, constraints: List['TypeConstraint']=None):
        super().__init__()
        self.name: IdNode = identifier
        self.constraints: List['TypeConstraint'] = constraints or []

    def accept(self, visitor: 'Visitor'):
        return visitor.visit_type_var(self)



class FunctionTypeNode(ASTNode):

    def __init__(self, arg_types: List[Union['TypeAnnotation', 'FunctionTypeNode']], return_type: Union[
        'TypeAnnotation', 'FunctionTypeNode']=None):
        super().__init__()
        self.args = arg_types
        self.return_type = return_type

    def accept(self, visitor: 'Visitor'):
        return visitor.visit_function_type(self)



class BlockNode(ASTNode):

    def __init__(self, stmts: List[ASTNode]):
        super().__init__()
        self.stmts = stmts

    def accept(self, visitor: 'Visitor'):
        return visitor.visit_block(self)

class FunctionCallNode(ASTNode):

    def __init__(self, call_source: ASTNode, args=None):
        super().__init__()
        self.call_source = call_source
        self.args: List[ASTNode] = args or []
        self.is_trait_function = False
        self.define_ast: FunctionDefNode = None
        self.trait_impl: 'TraitImpl' = None
        self.type_binds: dict[str, Any] = {}


    def accept(self, visitor: 'Visitor'):
        return visitor.visit_function_call(self)



class IndexNode(ASTNode):

    def __init__(self, target_node: VarNode, index_node: ASTNode):
        super().__init__()
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
        super().__init__()
        self.args = args

class LitDictNode(ASTNode):

    def __init__(self, args: List[Tuple[ASTNode, ASTNode]]):
        super().__init__()
        self.args = args

    def eval(self) -> Any:
        return dict(((x.eval(), y.eval()) for x, y in self.args))


class IfStatement(ASTNode):

    def __init__(self, branches: List[Tuple[ASTNode, BlockNode]], else_branch: Optional[BlockNode]):
        super().__init__()
        self.branches = branches
        self.else_branch = else_branch

    def accept(self, visitor: 'Visitor'):
        return visitor.visit_if(self)

class LoopStatement(ASTNode):
    def __init__(self, condition: ASTNode, body: BlockNode):
        super().__init__()
        self.condition = condition
        self.body = body

    def accept(self, visitor: 'Visitor'):
        return visitor.visit_loop(self)


class TypeAnnotation(ASTNode):
    def __init__(self, name: str, type_parameters: List['TypeVarNode']=None):
        super().__init__()
        self.name = name
        self.parameters: List['TypeVarNode'] = type_parameters or []

    def accept(self, visitor: 'Visitor'):
        return visitor.visit_type_annotation(self)


class TypeInstance(ASTNode):

    def __init__(self, name: str, type_parameters: List[Union['TypeVarNode', 'TypeInstance']]=None):
        super().__init__()
        self.name = name
        self.parameters = type_parameters or []

    @staticmethod
    def unit() -> 'TypeInstance':
        return TypeInstance("Unit")

    def accept(self, visitor: 'Visitor'):
        return visitor.visit_type_instance(self)


class StructDefNode(ASTNode):
    def __init__(self, name_and_param: TypeAnnotation, fields: List[Tuple[IdNode, TypeInstance]]):
        super().__init__()
        self.name_and_param = name_and_param
        self.fields = fields


    def accept(self, visitor: 'Visitor'):
        return visitor.visit_struct_def(self)


class VarDefNode(ASTNode):
    def __init__(self, var_node: IdNode, var_type: TypeInstance | FunctionTypeNode, init_expr: ASTNode=None):
        super().__init__()
        self.var_node = var_node
        self.var_type = var_type
        self.init_expr = init_expr

    def eval(self) -> Any:
        return None

    def accept(self, visitor: 'Visitor'):
        return visitor.visit_var_def(self)



class FunctionDefNode(ASTNode):

    def __init__(self, name: IdNode, args: List[VarDefNode], body: BlockNode, return_type: TypeInstance, trait_node: 'TraitImplNode', type_parameters: List['TypeVarNode'] = None):
        super().__init__()
        self.name = name
        self.args = args
        self.body = body
        self.return_type = return_type
        self.trait_node: TraitImplNode = trait_node
        self.type_parameters: List['TypeVarNode'] = type_parameters or []

    def accept(self, visitor: 'Visitor'):
        return visitor.visit_function_def(self)

class ProcNode(ASTNode):

    def __init__(self):
        super().__init__()
        self.children: List[ASTNode] = []

    def eval(self) -> Any:
        for child in self.children:
            child.eval()

    def accept(self, visitor: 'Visitor'):
        return visitor.visit_proc(self)

class ReturnNode(ASTNode):

    def __init__(self, expr: ASTNode=None):
        super().__init__()
        self.expr = expr

    def eval(self) -> Any:
        pass

    def accept(self, visitor: 'Visitor'):
        return visitor.visit_return(self)

class StructInitNode(ASTNode):

    def __init__(self, type_name: TypeInstance, body: List[Tuple[IdNode, ASTNode]]):
        super().__init__()
        self.type_name = type_name
        self.body = body
        self.type_ref: TypeRef = None

    def accept(self, visitor: 'Visitor') -> Any:
        return visitor.visit_struct_init(self)

class TraitFunctionNode(ASTNode):
    def __init__(self, name: IdNode, args: List[VarDefNode], return_type: TypeInstance):
        super().__init__()
        self.name = name
        self.args = args
        self.return_type = return_type

    def accept(self, visitor: 'Visitor'):
        return visitor.visit_trait_function(self)


class TraitNode(ASTNode):
    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def accept(self, visitor: 'Visitor'):
        return visitor.visit_trait_node(self)




class TraitDefNode(ASTNode):
    def __init__(self, name_and_param: TypeAnnotation, trait_functions: List[TraitFunctionNode]):
        super().__init__()
        self.name_and_param = name_and_param
        self.functions = trait_functions

    def accept(self, visitor: 'Visitor'):
        return visitor.visit_trait_def(self)

class TraitConstraintNode(ASTNode):

    def __init__(self, traits: List['TypeConstraint']):
        super().__init__()
        self.traits = traits

    def accept(self, visitor: 'Visitor'):
        return visitor.visit_trait_constraint(self)


class TraitImplNode(ASTNode):
    def __init__(self,
                 trait: 'TraitInstance',
                 target_type: TypeInstance,
                 functions: List[FunctionDefNode],
                 type_parameters: List['TypeVarNode']=None,
                 impl: 'TypeImpl'=None
                 ):
        super().__init__()
        self.trait = trait
        self.target_type = target_type
        self.functions = functions
        self.type_parameters = type_parameters or []
        self.impl_detail: TraitImpl = impl

    def accept(self, visitor: 'Visitor'):
        return visitor.visit_trait_impl(self)

    @property
    def trait_name(self):
        return self.trait.trait.name

class AttributeNode(ASTNode):

    def __init__(self, data: ASTNode, attr: IdNode):
        super().__init__()
        self.data = data
        self.attr = attr

    def accept(self, visitor: 'Visitor'):
        return visitor.visit_attribute(self)

class ContinueOrBreak(ASTNode):

    def __init__(self, kind: str):
        super().__init__()
        self.kind = kind

    def accept(self, visitor: 'Visitor'):
        return visitor.visit_continue_or_break(self)

class TypeParameters(ASTNode):
    def __init__(self, type_vars: List[TypeVarNode]):
        super().__init__()
        self.type_var = type_vars

    def accept(self, visitor: 'Visitor'):
        visitor.visit_generic_type(self)


class TypeConstraint(ASTNode):
    def __init__(self, trait: TraitNode, parameters: List[TypeInstance]=None):
        super().__init__()
        self.trait = trait
        self.parameters = parameters or []

    def accept(self, visitor: 'Visitor'):
        return visitor.visit_type_constraint(self)

class DynTraitNode(ASTNode):
    def __init__(self, trait_name: TraitNode):
        super().__init__()
        self.trait_name = trait_name

    def accept(self, visitor: 'Visitor'):
        return visitor.visit_dyn_trait(self)

TraitInstance = TypeConstraint