from typing import List, Optional
from dataclasses import dataclass

from parser.symbol_type import FunctionTypeRef, StructType, StructTypeRef, TraitTypeRef, TypeRef, PrimitiveType, \
    TypeVar, FunctionType


@dataclass
class Symbol:
    name: str

@dataclass
class VarSymbol(Symbol):
    type_ref: TypeRef
    type_deref: Optional[PrimitiveType | StructType | TypeVar]=None

@dataclass
class FunctionSymbol(Symbol):
    type_ref: FunctionTypeRef
    type_deref: Optional[FunctionType]=None

@dataclass
class TypeSymbol(Symbol):
    define: StructTypeRef|PrimitiveType
    parameters: List[TypeRef]

@dataclass
class GenericParamSymbol(Symbol):
    define: TypeRef

@dataclass
class TraitSymbol(Symbol):
    define: TraitTypeRef