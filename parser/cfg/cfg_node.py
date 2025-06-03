from typing import List
from parser.node import ASTNode
from dataclasses import dataclass, field


@dataclass
class BasicBlock:
    instructions: List[ASTNode] = field(default_factory=list)
    next_blocks: List['BasicBlock'] = field(default_factory=list)


EMPTY_BLOCK = BasicBlock()