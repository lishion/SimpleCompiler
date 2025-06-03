from dataclasses import dataclass
from typing import Dict, List

@dataclass
class PrimitiveType:
    name: str

@dataclass
class StructureType:
    name: str
    fields: Dict[str, 'Type']

@dataclass
class FunctionType:
    name: str
    parameters: List['Type']
    return_type: 'Type'

@dataclass
class TraitType:
    name: str
    impls: List[FunctionType]

@dataclass
class GenericParamType:
    name: str
    constraints: List[TraitType]


type Type = PrimitiveType | StructureType | FunctionType | TraitType | GenericParamType