from typing import Any, List

from parser.scope import Scope


class StackFrame:

    def __init__(self, scope: Scope, parent: 'StackFrame'=None):
        self.vars: dict[str, Any] = {}
        self.scope = scope
        self.parent = None

    def set(self, name: str, value: Any):
        self.vars[name] = value

    def get(self, name: str):
        return self.vars[name]

class Stack:

    def __init__(self, global_scope: Scope):
        self._stacks: List[StackFrame] = [StackFrame(global_scope)]

    def pop(self):
        return self._stacks.pop(-1)

    def push(self, stack: StackFrame):
        stack.parent = self.current
        self._stacks.append(stack)

    @property
    def current(self) -> StackFrame:
        return self._stacks[-1]