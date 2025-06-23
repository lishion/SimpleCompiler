from unittest import TestCase

from code_gen.script import PythonCodeGenerator
from parser.expr import parse_proc
from lexer.lexer import BaseLexer
from grammer import TOKENS
from parser.scope import ScopeManager, TraitImpls
from parser.visitor.script_gen_visitor import EvalVisitor
from parser.visitor.type_visitor import TypeDefVisitor, TypeDetailVisitor
from parser.utils import init_global_scope
from error.reporter import SourceCodeMaker
from runtime.data import MetaManager


class Test(TestCase):

    def get_tokens(self, code):
        return BaseLexer(TOKENS, SourceCodeMaker(code), code, ignore={"white_space", "comment"})

    def parse_tree(self, code):
        lexer = self.get_tokens(code)
        node = parse_proc(lexer)
        return node

    def parse(self, code):
        lexer = self.get_tokens(code)
        node = parse_proc(lexer)
        scope_manager = ScopeManager()
        init_global_scope(scope_manager)
        trait_impls = TraitImpls()
        TypeDefVisitor(scope_manager, trait_impls).visit_proc(node)
        TypeDetailVisitor(scope_manager, trait_impls).visit_proc(node)
        meta_manager = MetaManager()
        code_visitor = EvalVisitor(meta_manager, PythonCodeGenerator(), trait_impls)
        code_res = code_visitor.visit_proc(node)
        symbols = globals() | {'meta_manager': meta_manager}
        meta_manager.globals = symbols
        for func in code_visitor.function_defs:
            print(func)
            exec(func, symbols)
        print(code_res, flush=True)
        exec(code_res, symbols)

        return node, scope_manager, trait_impls

    def test(self):
        code = """
        
        trait List<T>{
            def add(t: T);
        }
        
        struct ArrayList<K>{
            item: K
        }
        
        trait T1<U>{
            def test(u: U);
        }
        
        impl <T, U> T1<T> for ArrayList<U>{
            def test(u: T) -> Unit{
                let x = 1;
            }
        }
        
        def get_list<T>(t: T) -> ArrayList<T>{
            let x = ArrayList{item: t};
            x.test(1);
            return x;
        }
        
        # impl <T, U> T1<T> for ArrayList<U1>
        # {
        #     U: T,
        # }
        
        # impl<T> List<T> for ArrayList<T>{
        #     def add(t: T) -> Unit{
        #         ArrayList{item: t}.test(1);
        #     }
        # }
        
 
      
        
        let x = get_list("1");
        #x.add(1);
        # x.add("123123");
 
        # struct Box<T, V>{
        #     item: T,
        #     item2: V
        # }
        # 
        # struct Converter{a: Int}
        # 
        # trait Convert<T, V>{
        #     def convert(t: T) -> V;
        # }
        # 
        # impl Convert<String, Int> for Converter{
        #     def convert(t: String) -> Int{
        #         return 1;
        #     } 
        # }
        # 
        # impl Into<String> for Box<String, Int>{
        #     def into() -> String{
        #         return "Box";
        #     }
        # }
        # 
        #  impl Into<Int> for Box<String, Int>{
        #     def into() -> Int{
        #         return 1;
        #     }
        # }
        # 
        # trait Into<T> {
        #     def into() -> T;
        # }
        # 
        # impl Into<String> for String{
        #     def into() -> String{
        #         return self;
        #     }
        # }
        # 
        # def b<T>(t: T) -> T{
        #     return t;
        # }
        # 
        # def c<T>(t: T) -> Box<T, T>{
        #     return Box{item: t, item2: t};
        # }
        # 
        #  def a(t1: String) -> Box<impl Into<String>, impl Convert<String, Int>>{
        #     return Box{item: t1, item2: Converter{a: 1}};
        # }
        # 
        # def get() -> Box<String, Int>{
        #     return Box{item: "1", item2: 2};
        # }
        
        # 
        # let x = a("1");
        # 
        # b(1);
        # 
        # let xxx = get();
        # 
        # let y1: Int = xxx.into();
        
        # struct A<T>{
        #     a: T
        # }
        # struct C<T>{}
        # 
        # struct B<X>{
        #     b: A<X>,
        #     c: X,
        #     d: String
        # }
        # 
        # trait Into<T>{
        #     def into() -> T;
        # }
        # 
        # trait Show{}
        # 
        # impl<X> Into<X> for String{
        #     def into() -> X{
        #         return self;
        #     }
        # }
        # 
        # 
        # 
        # 
        # let x = a("1");
        # 
        # let b = x.into();
        
        """
        _, scope_manager, trait_impls = self.parse(code)
        print(scope_manager.lookup_var("x"))
        print(scope_manager.lookup_var("y1"))
       #print(scope_manager.lookup_var("b"))
        # print(scope_manager.lookup_var("e"))
        # print(scope_manager.lookup_type('List'))
        # print(scope_manager.lookup_type('Node'))
        # print(scope_manager.lookup_traits('Convert'))
        #print(scope_manager.lookup_type('Pair'))
        #print(scope_manager.lookup_traits('Display'))
        #print(trait_impls.trait_impls)