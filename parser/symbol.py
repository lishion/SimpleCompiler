from typing import List, Optional
from dataclasses import dataclass

from parser.symbol_type import FunctionTypeRef, StructType, StructTypeRef, TraitTypeRef, TypeRef, PrimitiveType, \
    FunctionType, TypeVar, TraitRef


@dataclass
class Symbol:
    name: str

@dataclass
class VarSymbol(Symbol):
    type_ref: TypeRef | TypeVar
    type_deref: Optional[PrimitiveType | StructType ]=None

@dataclass
class FunctionSymbol(Symbol):
    type_ref: FunctionTypeRef
    type_deref: Optional[FunctionType]=None

@dataclass
class TypeSymbol(Symbol):
    define: StructTypeRef|PrimitiveType
    parameters: List[TypeRef|TypeVar]

@dataclass
class GenericParamSymbol(Symbol):
    define: TypeVar

@dataclass
class TraitSymbol(Symbol):
    define: TraitTypeRef