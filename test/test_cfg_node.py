from unittest import TestCase

from error.reporter import SourceCodeMaker, ErrorReporter
from grammer import TOKENS
from lexer.lexer import BaseLexer
from parser.cfg.cfg_node import BasicBlock, EMPTY_BLOCK
from parser.cfg.cfg_visitor import CFGVisitor
from parser.cfg.return_check import check_return
from parser.expr import parse_proc
from parser.node import *
from parser.scope import ScopeManager
from parser.utils import init_global_scope
from parser.visitor1 import PositionVisitor, SymbolVisitor, SymbolDefinitionVisitor, ReferenceResolveVisitor


def mock_binary_node(l, r):
    return  BinaryOpNode(
                '+',
                LiteralNode(l, 'Int'),
                LiteralNode(r, 'Int')
            )


def mock_condition_node(l, r):
    return  BinaryOpNode(
                '>',
                LiteralNode(l, 'Int'),
                LiteralNode(r, 'Int')
            )


class TestBasicBlock(TestCase):
    def get_tokens(self, code):
        return BaseLexer(TOKENS, SourceCodeMaker(code), code, ignore={"white_space", "comment"})

    def test_parse(self, code):
        lexer = self.get_tokens(code)
        node = parse_proc(lexer)

        # node.walk()
        scope_manager = ScopeManager()
        init_global_scope(scope_manager)
        reporter = ErrorReporter(SourceCodeMaker(code))
        PositionVisitor().visit_proc(node)
        cfg_visitor = CFGVisitor(reporter)
        return cfg_visitor.visit_proc(node)


    def test_check_return(self):
        entry_block = BasicBlock(
            instructions=[
                mock_binary_node(1, 2),
               mock_binary_node(3, 4)
            ],
            next_blocks=[
                BasicBlock(
                    instructions=[
                        mock_condition_node(1, 2)
                    ],
                    next_blocks=[
                        BasicBlock(
                            instructions=[
                                mock_binary_node(5, 6),
                                ReturnNode()
                            ],
                            next_blocks=[]
                        ),
                        EMPTY_BLOCK
                    ]
                )
            ]
        )
        r = check_return(entry_block)
        print(r)


    def test_build_cfg(self):
        code = """
            def func() -> Int{
                if a > 1{
                    let c = 1;
                    return;
                }elif a < 2{
                    if a > 1{
                        return;
                    }else{
                    
                    }
                }else{
                    let b = 1 + 2;
                    return;
                }
            }
        """
        rep = SourceCodeMaker(code)
        res = self.test_parse(code)
        for block in res:
            current = check_return(block)
            if current:
                print(rep.mark(start_position=current.instructions[0].start_pos, end_position=current.instructions[0].end_pos))
