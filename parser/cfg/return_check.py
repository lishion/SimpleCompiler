from parser.node import ReturnNode
from parser.cfg.cfg_node import BasicBlock

def check_return(block: BasicBlock):
    for instruction in block.instructions:
        if isinstance(instruction, ReturnNode):
            return None
    if not block.next_blocks:
        return block
    for next_block in block.next_blocks:
        if res := check_return(next_block):
            print(res, next_block.instructions)
            return res
    return None