from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union

@dataclass
class PrimitiveType:
    name: str


@dataclass
class TypeRef:
    # 类型名字
    name: str
    # 类型参数列表，比如 A<K, V> 那么 parameters [K, V]
    parameters: List['TypeRef'] = field(default_factory=list)
    # 类型带的约束，例如 struct A<T: (Read + Write)> = {a: T}，此时 T 的约束为 Read + Write
    constraints: List['TraitRef'] = field(default_factory=list)
    # 是一个类型变量，还是具体类型
    is_var: bool = False

    struct_ref: Optional['StructTypeRef']=None

    @property
    def is_primitive_type(self):
        return self.name in (
            "Float",
            "Int",
            "Bool",
            "String",
            "Any"
        )

    def __str__(self):
        if self.parameters:
            string = f'<{", ".join(map(str, self.parameters))}>'
        else:
            string = ''
        if self.constraints:
            cons = f':({", ".join(map(str, self.constraints))})'
        else:
            cons = ''
        return f"{self.name}{string}{cons}"

    def __eq__(self, other: 'TypeRef'):
        if self.is_var and other.is_var and self.constraints == other.constraints:
            return True
        else:
            return self.name == other.name and self.parameters == other.parameters

    def eq_type_only(self, other: 'TypeRef'):
        return self.is_var and other.is_var or self.name == other.name

    def __repr__(self):
        return self.__str__()

    @staticmethod
    def type_var(name: str, constraints: List['TraitRef'] = None) -> 'TypeRef':
        return TypeRef(name=name, parameters=[], constraints=constraints, is_var=True)

@dataclass
class TypeVar:
    name: str
    constraints: List['TraitRef'] = field(default_factory=list)


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
    parameters: List['TypeRef'] = field(default_factory=list)

@dataclass
class StructType:
    name: str
    fields: Dict[str, Union['StructType', PrimitiveType]]

@dataclass
class FunctionTypeRef:
    name: Optional[str]
    args: List['TypeRef']
    return_type: 'TypeRef'
    type_parameters: List['TypeRef'] = field(default_factory=list)
    association_type: Optional['TraitTypeRef'] = None

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
    parameters: List['TypeRef'] = field(default_factory=list)

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
    type_parameters: List[TypeRef] = field(default_factory=list)
    functions: Dict[str, FunctionTypeRef] = field(default_factory=dict)

@dataclass
class MultiResolvedFunction:
    functions: List[FunctionTypeRef]

type ValueType = PrimitiveType | StructTypeRef | FunctionTypeRef | TraitTypeRef
type Type = ValueType