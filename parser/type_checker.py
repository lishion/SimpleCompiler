from dataclasses import dataclass
from parser.types import BaseType, is_primitive_type

@dataclass
class TypeCheckResult:
    generic_types: dict[str, str]


def type_check(expect_type: BaseType, impl_type: BaseType):
    kind1 = type(expect_type)
    kind2 = type(impl_type)
    if kind1 is not kind2:
        raise TypeError("can not convert from {} to {}".format(kind1, kind2))
    if expect_type.name != impl_type.name:
        raise TypeError("can not convert from {} to {}".format(expect_type, impl_type))
    if expect_type