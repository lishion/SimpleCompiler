from enum import Enum
from dataclasses import dataclass

class VarType(Enum):
    Int = "Int"
    Float = "Float"
    String = "String"
    Bool = "Bool"
    Unit = "Unit"


@dataclass
class Type:
    name: str