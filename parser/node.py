from typing import List, Any
from dataclasses import dataclass, field
from abc import ABC, abstractmethod


@dataclass
class ASTNode(ABC):
    text: str
    node_type: str
    children: List['ASTNode'] = field(repr=False, default_factory=list)

    def walk(self):
        def helper(ast: 'ASTNode', layer):
            print('    ' * layer, ast)
            for child in ast.children:
                helper(child, layer + 1)

        helper(self, 0)

    @abstractmethod
    def eval(self) -> Any: pass

IDS = {}

@dataclass
class BinaryOpNode(ASTNode):
    node_type: str = "bin_op"

    def eval(self) -> Any:
        if self.text == "=":
            key = self.children[0].text
            value = self.children[1].eval()
            IDS[key] = value
            return value
        return eval(f"{self.children[0].eval()} {self.text} {self.children[1].eval()}")





@dataclass
class LiteralNode(ASTNode):

    def eval(self) -> Any:
        if self.node_type == "int":
            return int(self.text)
        if self.node_type == "float":
            return float(self.text)
        if self.node_type == "lit":
            return self.text
        if self.node_type == "id":
            if self.text not in IDS:
                raise Exception(f"undefined var {self.text}")
            return IDS[self.text]
        return self.text


@dataclass
class StmtNode(ASTNode):
    node_type: str = "stmt"

    def eval(self) -> Any:
        res = None
        for child in self.children:
           res = child.eval()
        return res