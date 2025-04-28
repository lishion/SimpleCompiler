from unittest import TestCase
from parser.expr import parse_proc
from lexer.lexer import BaseLexer
from grammer import TOKENS
from parser.scope import ScopeManager
from parser.visitor import SymbolVisitor, ReferenceResolveVisitor, EvalVisitor
from parser.utils import init_global_scope
from rich import print as rprint

class Test(TestCase):

    def test_parse(self, code):
        lexer = BaseLexer(TOKENS, code, ignore="white_space")
        return parse_proc(lexer)

    def test_add(self):
        node = self.test_parse("""
               let a = 1 + 1;
               """)
        node.walk()

    def test_parse_func_call(self):
        node = self.test_parse("""
              test(1+2);
              b=1;
              a+1;
              test(1+2, a+2, 3333) + test1(1, 2, 3,);
               """)
        node.walk()

    def test_parse_mul(self):
        # lexer = BaseLexer(TOKENS, '[1, 2, 3, 4+5, 3==1];', ignore="white_space")
        # left = parse_stmt(lexer)
        # left.walk()
        # print(left.eval())
        # print(IDS)
        #
        # lexer = BaseLexer(TOKENS, '{1: 2, "3": 4, 1+4: 5+6};', ignore="white_space")
        # left = parse_stmt(lexer)
        # left.walk()
        # print(left.eval())
        # print(IDS)
        #
        # lexer = BaseLexer(TOKENS, 'a={1: 2, "3": 4, 1+4: 5+6}; print(a);', ignore="white_space")
        # left = parse_stmt(lexer)
        # left.walk()
        # print(left.eval())
        # print(IDS)

        self.test_parse("""
        if 2 == 2{
            print("true");
        } 
        else{
            print("false");
        }
        """).walk()
        # print(left.eval())
        # print(IDS)

    def test_parse_while(self):
        self.test_parse(
            """
            while()
            """
        )

    def test_parse_func(self):
        node = self.test_parse("""
            def hello(name, dd){
                a = name + 2;
                b = a + dd;
            }
            a = hello(2, 1);
            print(a);
            a = 1;
            b = 2;
            if a >= 1{
                print("hello");
            }
            if b < 0{
                print("world");
            }
        """)
        print(node)
        print(node.eval())

    def test_parse_func(self):
        node = self.test_parse("""
           def hello(name: String, dd: Int, ){
            a = name + 2;
           }
        """)
        node.walk()
        # print(node.eval())

    def test_var_decl(self):
        node = self.test_parse('''
            let a = "1";
            def f(a: Int, b: String): String{
                return b;
            }
            let b = f(1, "2");
        ''')
        node.walk()
        scope_manager = ScopeManager(init_global_scope())
        SymbolVisitor(scope_manager).visit_proc(node)
        ReferenceResolveVisitor().visit_proc(node)

    def test_type_def(self):
        node = self.test_parse("""
        type Student = {
            name: String,
            id: Int
        }
        """)
        print(node.walk())

    def test_var_def(self):
        node = self.test_parse("""
        let a : Int;
        let a: Int = 1;
        let a = 1;
        let b: String = a + 1;
        b = 1;
        """)
        print(node)

    def test_build_symbol(self):
        node = self.test_parse("""
               let a : Int;
               type Student = {
                   name: String,
                   id: Int
               }
               let a = 1;
               def fun(b: Int, a: Int): Int{
                    let c = 1;
                    if a >= 2{
                       let d = 1;
                       let a = 2;
                       return 1;
                    }
                    
                    let d = 1;
                    return "1";
               }
               type Id = {
                value: Int
               }
               """)
        node.walk()

        # scope_manager = ScopeManager(init_global_scope())
        # SymbolVisitor(scope_manager).visit_proc(node)
        # scope_manager.show()
        # BNF
        # a -> ""

    def test_eval(self):
        node = self.test_parse("""
          let 123;
          def test(a: String): String{
              return a;
           }
           def test(b: Int): Int{
              return b;
           }
           print(a123);
           print(test("1"));
        """)
        node.walk()
        scope_manager = ScopeManager(init_global_scope())
        SymbolVisitor(scope_manager).visit_proc(node)
        ReferenceResolveVisitor().visit_proc(node)
        EvalVisitor(scope_manager.global_scope).visit_proc(node)

    def test_rich(self):
        code = """
        1 | func add(a, b) {
        2 |     return a + b
        3 | }
        4 | 
        5 | add(1, "2")  # 类型错误
        """

        # 高亮错误行
        rprint(code)