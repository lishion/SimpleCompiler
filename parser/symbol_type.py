from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Any
from uuid import uuid4

@dataclass
class PrimitiveType:
    name: str

@dataclass(frozen=True)
class TypeVar:
    name: str
    id: str
    # 类型带的约束，例如 struct A<T: (Read + Write)> = {a: T}，此时 T 的约束为 Read + Write
    constraints: List['TraitRef'] = field(default_factory=list)
    is_var = True
    is_primitive_type = False

    def __eq__(self, other: 'TypeVar'):
        if not isinstance(other, TypeVar):
            return False
        return other.id == self.id and other.name == self.name

    def __hash__(self) -> int:
        return hash((self.id, self.name))

    @staticmethod
    def create(name: str, constraints: Optional[List['TraitRef']] = None):
        constraints = constraints or []
        return TypeVar(name, str(uuid4()), constraints)

    @staticmethod
    def is_a_var(obj: Any) -> bool:
        return isinstance(obj, TypeVar)

@dataclass
class TypeRef:
    # 类型名字
    name: str
    # 类型参数列表，比如 A<K, V> 那么 parameters [K, V]
    parameters: List[Union['TypeRef', TypeVar]] = field(default_factory=list)
    struct_ref: Optional['StructTypeRef']=None
    is_var = False
    @property
    def is_primitive_type(self):
        return self.name in (
            "Float",
            "Int",
            "Bool",
            "String",
            "Any",
            "Unit"
        )

    def __str__(self):
        if self.parameters:
            string = f'<{", ".join(map(str, self.parameters))}>'
        else:
            string = ''
        # if self.constraints:
        #     cons = f':({", ".join(map(str, self.constraints))})'
        # else:
        cons = ''
        return f"{self.name}{string}{cons}"

    def __eq__(self, other: 'TypeRef'):
        if self.name != other.name:
            return False
        if self.parameters:
            return self.parameters == other.parameters

        return True

        # if self.is_var and other.is_var and self.constraints == other.constraints:
        #     return True
        # else:
        #     return self.name == other.name and self.parameters == other.parameters

    # def eq_type_only(self, other: 'TypeRef'):
    #     return self.is_var and other.is_var or self.name == other.name

    def __repr__(self):
        return self.__str__()

    # @staticmethod
    # def type_var(name: str, constraints: List['TraitRef'] = None) -> 'TypeVar':
    #     return TypeVar(name, str(uuid4()), constraints)


@dataclass
class TraitRef:
    # trait 的名字
    name: str
    # trait 的参数列表
    parameters: List['TypeRef'] = field(default_factory=list)

    def __str__(self):
        if self.parameters:
            string = f'<{",".join(map(str, self.parameters))}>'
        else:
            string = ''
        return f"{self.name}{string}"

    def __eq__(self, other: 'TraitRef'):
        return self.name == other.name and self.parameters == other.parameters

    def __repr__(self):
        return self.__str__()



@dataclass
class Constraint:
    traits: List['TraitTypeRef'] = field(default_factory=list)

@dataclass
class StructTypeRef:
    name: str
    fields: Dict[str, 'TypeRef']
    parameters: List[Union['TypeRef', 'TypeVar']] = field(default_factory=list)

@dataclass
class StructType:
    name: str
    fields: Dict[str, Union['StructType', PrimitiveType]]

@dataclass
class FunctionTypeRef:
    # from parser.node import FunctionDefNode
    name: Optional[str]
    args: List[Union['TypeRef', TypeVar]]
    return_type: 'TypeRef'
    type_parameters: List['TypeRef'] = field(default_factory=list)
    association_impl: Optional['TraitImpl'] = None
    association_trait: Optional['TraitRef'] = None
    association_ast: Optional['FunctionDefNode'] = None
    call_source_type: Optional[TypeRef|TypeVar] = None

@dataclass
class FunctionType:
    name: Optional[str]
    args: List[StructType|PrimitiveType]
    return_type: StructType|PrimitiveType
    type_parameters: List[StructType|PrimitiveType] = field(default_factory=list)
    association_type: Optional['TraitTypeRef'] = None


@dataclass
class TraitTypeRef:
    name: str
    functions: Dict[str, FunctionTypeRef] = field(default_factory=dict)
    parameters: List['TypeVar'] = field(default_factory=list)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        if self.parameters:
            string = f'<{self.parameters}>'
        else:
            string = ''
        return f"{self.name}{string}"


@dataclass
class TraitImpl:
    trait: TraitRef
    target_type: TypeRef
    type_parameters: List[TypeRef|TypeVar] = field(default_factory=list)
    functions: Dict[str, FunctionTypeRef] = field(default_factory=dict)

@dataclass
class MultiResolvedFunction:
    functions: List[FunctionTypeRef]

type ValueType = PrimitiveType | StructTypeRef | FunctionTypeRef | TraitTypeRef
type Type = ValueType