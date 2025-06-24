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
        symbols = globals() | {'meta_manager': meta_manager}
        meta_manager.globals = symbols
        code_visitor = EvalVisitor(meta_manager, PythonCodeGenerator(), trait_impls)
        code_res = code_visitor.visit_proc(node)
        for func in code_visitor.function_defs:
            print(func)
            exec(func, symbols)
        print(code_res, flush=True)
        exec(code_res, symbols)
        return node, scope_manager, trait_impls

    def test(self):
        code = """
        
        struct Pair<K, V>{
            key: K,
            value: V
        }
        
        def make_pair<K, V>(k: K, v: V) -> Pair<K, V>{
            return Pair{key: k, value: v};
        }
        
        
        let x = make_pair(1, "2");
        echo(x);
        
        trait List<T>{
            def add(t: T);
        }
        
        def xxx() -> impl Convert<String>{
            return 123123123;
        }
        
        let cddd = xxx();
        echo(cddd);

        struct ArrayList<K>{
            item: K
        }

        trait T1<U>{
            def test(u: U);
        }
        
        # def print_hello() -> Unit{
        #     write_line("hello world");
        # }
        # 
        # print_hello();
        
        
        impl <T: Convert<String>, U: Convert<String>> T1<T> for ArrayList<U>{
            def test(u: T) -> Unit{
                let x = 1;
                echo(u.to());
            }
        }

        trait Convert<T>{
            def to() -> T;
        }

        impl Convert<String> for Int{
            def to() -> String{
                return as_string(self);
            }
        }

        def write_line<T: Convert<String>>(t: T) -> Unit{
            echo(t.to());
        }
        
        def a<T>(x: T) -> T{
            return x;
        }
        
        def b<T>(x: T) -> T{
            return a(x);
        }
        
        def c<T>(x: T) -> T{
            return b(x);
        }
        

    

        def get_list<T: Convert<String>>(t: T) -> ArrayList<T>{
            let x = ArrayList{item: t};
            x.test(t);
            return x;
        }
        
        
        def d<T>(x: T) -> T{
            return x;
        }
        
        def e<T>(x: T) -> T{
            return x;
        }
        
        def f<T>(x: T) -> T{
            return x;
        }
        
        # let xxx = c(1);
        # echo(xxx);
        
        let yyy = d(e(f(1)));
        echo(yyy);
        
        # impl <T, U> T1<T> for ArrayList<U1>
        # {
        #     U: T,
        # }
        
        # impl<T> List<T> for ArrayList<T>{
        #     def add(t: T) -> Unit{
        #         ArrayList{item: t}.test(1);
        #     }
        # }
        
        
        # write_line(1);
        # 
        # 
        let x1 = get_list(1);
        #x1.add(1);
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
        # print(scope_manager.lookup_var("x"))
        # print(scope_manager.lookup_var("y1"))
       #print(scope_manager.lookup_var("b"))
        # print(scope_manager.lookup_var("e"))
        # print(scope_manager.lookup_type('List'))
        # print(scope_manager.lookup_type('Node'))
        # print(scope_manager.lookup_traits('Convert'))
        #print(scope_manager.lookup_type('Pair'))
        #print(scope_manager.lookup_traits('Display'))
        #print(trait_impls.trait_impls)

    def test_dyn_trait(self):
        code = """
        trait Converter<T>{
            def into() -> T;
        }
        
        impl Converter<String> for Int{
            def into() -> String{
                echo("c to string");
                return as_string(self);
            }
        }
        
        def get_dyn() -> impl Converter<String>{
            return 1;
        }
        
        let c = get_dyn();
        let yyy: String = c.into();
        echo(yyy);

        """
        _, scope_manager, trait_impls = self.parse(code)
        print(scope_manager.lookup_var("c"))
        # print(scope_manager.lookup_var("y1"))
        # print(scope_manager.lookup_var("b"))
        # print(scope_manager.lookup_var("e"))
        # print(scope_manager.lookup_type('List'))
        # print(scope_manager.lookup_type('Node'))
        # print(scope_manager.lookup_traits('Convert'))
        # print(scope_manager.lookup_type('Pair'))
        # print(scope_manager.lookup_traits('Display'))
        # print(trait_impls.trait_impls)