import dataclasses
from abc import abstractmethod
from collections import defaultdict
from typing import Dict, Any, Callable, DefaultDict
from dataclasses import field


@abstractmethod
class FunctionObject:

    @abstractmethod
    def call(self, *args, **kwargs): pass

    def __call__(self, *args, **kwargs):
        return self.call(*args, **kwargs)

@abstractmethod
class CodeFunctionObject(FunctionObject):

    def call(self, *args, **kwargs):
        return self.code(*args, **kwargs)

    def __init__(self, code: Callable):
        self.code = code


class NameFunctionObject(FunctionObject):

    def call(self, *args, **kwargs):
        return eval(self.function_name, self.globals)(*args, **kwargs)

    def __init__(self, function_name: str, globals: Dict[str, Any]):
        self.function_name = function_name
        self.globals = globals

@dataclasses.dataclass
class DataMeta:
    name: str
    vtable: DefaultDict[str, DefaultDict[str, FunctionObject]] = field(default_factory=lambda: defaultdict(defaultdict))


class DataObject:
    def __init__(self, data: Dict[str, Any]|Any, meta: DataMeta):
        self.data = data
        self.meta: DataMeta = meta

    def get_function(self, name: str) -> DefaultDict[str, FunctionObject]:
        return self.meta.vtable.get(name)

    def attr(self, name: str) -> Any:
        if name in self.meta.vtable:
            return self.meta.vtable[name]
        return self.data.get(name)

class MetaManager:

    def __init__(self):
        self.metas: Dict[str, DataMeta] = {}
        # self.global_vtable: DefaultDict[str, DataMeta] = DataMeta()
        self.globals = {}

    def create_object(self, name: str, data: Dict[str, Any]) -> DataObject:
        meta = self.metas[name]
        return DataObject(data, meta)

    def add_meta(self, meta: DataMeta):
        self.metas[meta.name] = meta

    def get_or_create_meta(self, name: str) -> DataMeta:
        if name not in self.metas:
            self.metas[name] = DataMeta(name)
        return self.metas[name]