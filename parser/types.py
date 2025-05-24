from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Dict, Union


class VarType(Enum):
    Int = "Int"
    Float = "Float"
    String = "String"
    Bool = "Bool"
    Unit = "Unit"
    Any = "Any"


def is_primitive(name: str) -> bool:
    return name in VarType.__members__



@dataclass
class Kind:
    pass

@dataclass
class Type:
    name: str

    def __hash__(self) -> int:
        return hash(self.name)

    def replace_type_var(self, type_var, target_type):
        if self.name == type_var:
            return Type(target_type)
        return self

    def is_self(self):
        return self.name == "Self"

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()

@dataclass
class FunctionSignature:
    args: Tuple[Union[Type, 'FunctionSignature', 'TraitConstraintsType'], ...]
    return_type: Union[Type, 'FunctionSignature', 'TraitConstraintsType']
    is_trait_function: bool = False

    def __str__(self):
        args = ', '.join(map(lambda x: x.name if isinstance(x, Type) else str(x), self.args))
        return f"({args})" + "->" + (self.return_type.name if isinstance(self.return_type, Type) else str(self.return_type))

    def __hash__(self) -> int:
        return hash((self.args, self.return_type))

    def replace_type_var(self, type_var, target_type):

        def replace(t):
            if isinstance(t, Type) and t.name == type_var:
                return Type(target_type)
            elif isinstance(t, FunctionSignature):
                return t.replace_type_var(t, target_type)
            else:
                return t

        args = [replace(arg_type) for arg_type in self.args]
        return_type = replace(self.return_type)
        return FunctionSignature(tuple(args), return_type)


@dataclass
class FunctionOverloadType:
    overloads: List[FunctionSignature]

@dataclass
class TraitType:
    traits: List[FunctionSignature]

@dataclass
class StructureType:
    types: Dict[str, Union[Type, FunctionSignature, FunctionOverloadType, 'StructureType']]

@dataclass
class TraitConstraintsType:
    constraints: List[str]


def resolve(t: Type, scope: 'Scope'):
    if isinstance(t, Type):
        if is_primitive(t.name):
            return t
        structure = scope.lookup_type(t.name)
        return StructureType({name: resolve(t, scope) for name, t in structure.type_def.types.items()})
    return StructureType({name: resolve(t1, scope) for name, t1 in t.types.items()})


type Types = Kind | Type | FunctionSignature | FunctionOverloadType | StructureType | StructureType
type BaseType = Type | FunctionSignature | StructureType

UNIT = Type("Unit")