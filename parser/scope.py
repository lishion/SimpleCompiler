from typing import Dict, AnyStr, Any, Optional

class Scope:

    UNDEFINED = None

    def __init__(self):
        self.parent: Optional['Scope'] = None
        self.names: Dict[AnyStr, Any] = {}

    def lookup(self, name: AnyStr):
        if name in self.names:
            return self.names[name]
        if not self.parent:
            raise ValueError(f"var {name} not found")
        return self.parent.lookup(name)

    def set(self, name, value):
        self.names[name] = value


GLOBAL_SCOPE = Scope()

GLOBAL_SCOPE.set("print", print)


class ScopeManager:

    def __init__(self, global_scope: Scope):
        self.global_scope = global_scope
        self.current_scope: Scope = global_scope

    def enter(self):
        current = self.current_scope
        self.current_scope = Scope()
        self.current_scope.parent = current

    def exit(self):
        self.current_scope = self.current_scope.parent

    @property
    def current(self) -> Scope:
        return self.current_scope

SCOPE_MANAGER = ScopeManager(GLOBAL_SCOPE)