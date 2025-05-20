from typing import Dict, Optional
from runtime import FunctionObject
from collections import defaultdict

class Vtable:

    def __init__(self):
        self.vtable: Dict[str, Dict[str, FunctionObject]] = defaultdict(dict)

    def add(self, data_type: str, func_name: str, func: FunctionObject):
        self.vtable[data_type][func_name] = func

    def get(self, data_type: str, func_name: str) -> Optional[FunctionObject]:
        return self.vtable.get(data_type, {}).get(func_name, {})