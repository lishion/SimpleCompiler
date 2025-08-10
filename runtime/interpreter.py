from code_gen.script import PythonCodeGenerator
from error.reporter import SourceCodeMaker
from lexer.lexer import BaseLexer
from lexer.tokendef import TokenFactory
from parser.scope import TraitImpls
from parser.symbol import TypeSymbol
from parser.symbol_type import PrimitiveType
from parser.visitor.script_gen_visitor import EvalVisitor
from grammer import TOKENS
from runtime.bridge import BRIDGE_CODE
from runtime.bridge.native_function import NativeFunction, NATIVE_MANAGER, NativeManager
from parser.expr import parse_proc
from parser.visitor.type_visitor import TypeDefVisitor, TypeDetailVisitor
from functools import partial

PRIMITIVE_TYPE_NAME = [
    "Int",
    "String",
    "Float",
    "Bool",
    "Unit",
    "Any"
]

class Interpreter:
    def __init__(self, native_manager: NativeManager,
                 trait_impls: TraitImpls,
                 token_factory: TokenFactory):
        self._native_funcs = native_manager.native_functions
        self._meta_manager = native_manager.meta_manager
        self._scope_manager = native_manager.scope_manager
        self._token_factory = token_factory
        self._trait_impls = trait_impls
        self._runtime_symbols = None
        self._native_func_obj = NativeFunction(self._meta_manager)

    def _native_functions(self):
        return {name: partial(func['func'], self._native_func_obj) for name, func in self._native_funcs.items()}

    @staticmethod
    def get_ast(source):
        lexer = BaseLexer(TOKENS, SourceCodeMaker(source), source, ignore={"white_space", "comment"})
        node = parse_proc(lexer)
        return node

    def init(self):
        node = self.get_ast(BRIDGE_CODE)
        for t in PRIMITIVE_TYPE_NAME:
            self._scope_manager.add_type(TypeSymbol(t, define=PrimitiveType(t), parameters=[]))
            self._meta_manager.get_or_create_meta(t)

        symbols = globals() | {'meta_manager': self._meta_manager} | self._native_functions()
        self._meta_manager.globals = symbols

        TypeDefVisitor(self._scope_manager, self._trait_impls).visit_proc(node)
        TypeDetailVisitor(self._scope_manager, self._trait_impls).visit_proc(node)


    def run(self, source):
        node = self.get_ast(source)
        TypeDefVisitor(self._scope_manager, self._trait_impls).visit_proc(node)
        TypeDetailVisitor(self._scope_manager, self._trait_impls).visit_proc(node)
        code_visitor = EvalVisitor(self._meta_manager, PythonCodeGenerator(), self._trait_impls)
        code_res = code_visitor.visit_proc(node)
        for func in code_visitor.function_defs:
            #print(func)
            exec(func, self._meta_manager.globals)
        #print(code_res, flush=True)
        exec(code_res, self._meta_manager.globals)

INTERPRETER = Interpreter(
    NATIVE_MANAGER,
    trait_impls=TraitImpls(),
    token_factory=TOKENS
)

