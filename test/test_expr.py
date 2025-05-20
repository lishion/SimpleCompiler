from unittest import TestCase

from code_gen.byte_code_generator import BytecodeGenerateVisitor
from code_gen.indent import PythonCodeGenerator
from parser.expr import parse_proc
from lexer.lexer import BaseLexer
from grammer import TOKENS
from parser.scope import ScopeManager
from parser.types import FunctionSignature
from parser.visitor import SymbolVisitor, ReferenceResolveVisitor, EvalVisitor, PositionVisitor, SymbolDefinitionVisitor
from parser.utils import init_global_scope
from error.reporter import SourceCodeMaker, ErrorReporter
from runtime.data import MetaManager
from runtime import *

class Test(TestCase):

    def get_tokens(self, code):
        return BaseLexer(TOKENS, SourceCodeMaker(code), code, ignore={"white_space", "comment"})

    def parse_tree(self, code):
        lexer = self.get_tokens(code)
        node = parse_proc(lexer)
        return node

    def test_parse(self, code):
        lexer = self.get_tokens(code)
        node = parse_proc(lexer)

        # node.walk()
        scope_manager = ScopeManager()
        init_global_scope(scope_manager)
        reporter = ErrorReporter(SourceCodeMaker(code))
        PositionVisitor().visit_proc(node)
        SymbolVisitor(scope_manager, reporter).visit_proc(node)
        SymbolDefinitionVisitor(reporter).visit_proc(node)
        reporter.report_all()
        ReferenceResolveVisitor(reporter).visit_proc(node)
        return node, scope_manager

    def test_undefined(self, code):
        lexer = BaseLexer(TOKENS, SourceCodeMaker(code), code, ignore={"white_space", "comment"})
        node = parse_proc(lexer)
        # node.walk()
        scope_manager = ScopeManager()
        init_global_scope(scope_manager)
        reporter = ErrorReporter(SourceCodeMaker(code))
        PositionVisitor().visit_proc(node)
        SymbolVisitor(scope_manager, reporter).visit_proc(node)
        SymbolDefinitionVisitor(reporter).visit_proc(node)
        reporter.report_all()

    def test_parse_tree(self):
        self.parse_tree(
            """
            type A = {
                a: Int,
                b: String,
            }
            
            def a(b: String, c: (String) -> Unit) -> (Int) -> String{
            }
            
            trait Show(T){
               def show(t: T) -> String
            }
            
            impl Show for A{
                def show(t: A) -> String{
                    return self.name;
                }
            }
            
            def a(b: impl A, b: impl (A+B)) -> String{
            
            }
            
            let a: ((String)->Int, Int) -> (Int) -> String;
            
            let a = b.c.d + 1;
            
            let a = b.c.d(a.b.c() + a.c) + 1;
           
            let b = b().c;
            
            let c = A{
              b = B{
                 c = 1
              },
            };
            """
        ).walk()


    def test_ast_to_type(self):
        node = self.parse_tree('let a: ((String)->Int, Int) -> (Int) -> String;')
        function_type_node = node.children[0].var_type
        from parser import utils
        t = utils.extract_type_from_ast(function_type_node)

        self.assertTrue(type(t) == FunctionSignature)
        self.assertTrue(type(t.return_type) == FunctionSignature)
        self.assertTrue(type(t.args[0]) == FunctionSignature)

    def test_parse_trait(self):
        self.test_parse("""
                # type ID = {
                #     val: Int
                # }
                # type Student = {
                #     a: Int, 
                #     b: String, 
                #     c: ID,
                #     d: (Int) -> String
                # }
                # trait Show(T){
                #     def show(self: T) -> String
                #     # def show2(self: T) -> String
                # }
                # 
                # impl Show for Student{
                #     def show(self: Student) -> String{
                #         return "123";
                #     }
                # }
               
                let a = Student{
                    a = 1,
                    b = "1",
                    c = ID{
                        val = 1
                    }
                    show = 4
                };
                
                # def test(a: String) -> Unit{
                # 
                # }
                # 
                # let c = a.show();
                
        """)

    def test_parse_function(self):
        self.test_parse("""
                def a() -> Unit{
                
                }
                let b: () -> String = a;
        """)


    def test_undefined_error(self):
        self.test_undefined("let a = b11 + 1;")
        self.test_undefined("let a: B11 = b;")
        self.test_undefined("def a(a: NoType1) -> NoType{}")
        self.test_undefined("type A = {b: NoType}")
        self.test_undefined("let a: (String) -> NoType;")
        self.test_undefined("a();")
        self.test_undefined("def a() ->  Unit {return b;}")
        self.test_undefined("a=1;")
        self.test_undefined("""
             impl Show for Student{
                    def show(self: Student) -> String{
                        return "123";
                    }
                }
        """)

    def test_type_resolve(self):
        self.test_parse("def a(n: String): String{} a(1);")

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
                   id: Name
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

        scope_manager = ScopeManager(init_global_scope())
        SymbolVisitor(scope_manager).visit_proc(node)
        scope_manager.show()


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


    def test_eval(self):
        source = """
         type A = {
          name: Name,
         }
        """
        node = self.test_parse(source)
        node.walk()
        scope_manager = ScopeManager(init_global_scope())
        SymbolVisitor(scope_manager).visit_proc(node)
        ReferenceResolveVisitor(SourceCodeMaker(source)).visit_proc(node)
        EvalVisitor(scope_manager.global_scope).visit_proc(node)

    def test_eval(self):
        source = """
        type Student = {name: String, f: Function}
        type Function = {call: (String) -> Unit}
        
        impl Write for Student {
            def toString() -> String{
                if 2 > 1{
                    return "1";
                }elif 43 > 1{
                    let a = 1 + 2;
                    if 4 > 5{
                        return "9";
                    }
                    return "11";
                }else{
                    return "2";
                }
                return "Student{name=" + self.name + "}";
            }
        }
        
        def echo(t1: impl Write) -> Unit{
             print(t1.toString());
        }
        
        let f = Function{
            call = print,
        };
        
        let s = Student{
                name = "123",
                f = f
            };
        
        echo(s);
        
        f.call("hello world");
        s.f.call("nihao");

        """

        node, scope_manager = self.test_parse(source)
        meta_manager = MetaManager()
        code_generator = PythonCodeGenerator()
        code = EvalVisitor(scope_manager.global_scope, meta_manager, code_generator).visit_proc(node)
        print(code)
        exec (code)

    def test_failed(self):
        source = """
        let s = Student{
                name = "123"
            };
        type Student = {name: String}
        type Function = {call: (String) -> Unit}
        def test(a: impl Write, b: String) -> Unit{
            
        }
        impl Write for Student {
            def toString() -> String{
                return self.name;
            }
        }
        test(s, 1);
        # 
        def echo(t1: impl Write) -> Unit{
             print(t1.toString());
        }
        # 
        # let f = Function{
        #     call = print,
        # };
        # 
        # let s = Student{
        #         name = "123",
        #         f = f
        #     };
        # 
        #echo(s);
        # 
        # 
        # f.call("hello world");
        # s.f.call("nihao");

        """

        node, scope_manager = self.test_parse(source)
        meta_manager = MetaManager()
        code = EvalVisitor(scope_manager.global_scope, meta_manager).visit_proc(node)
        print(code)
        #exec(code)

    def test_code_gen(self):
        source = """

        
        type Student = {
            name: String,
            age: Int,
            id: ID,
        }
        
        type ID = {
            id: String
        }
        impl Write for Student {
            def toString() -> String{
                return self.name;
            }
        }
        
        def test(s: impl Write) -> Unit{
            echo(s.toString());
        }
        # 
        let stu = Student{
            name = "lily",
            age = 10,
            id = ID{
                id = "20"
            }
        };
        test(stu);
        """
        from collections import defaultdict


        node, scope_manager = self.test_parse(source)
        bytecode_obj = BytecodeGenerateVisitor().visit_proc(node)
        print('varnames:', bytecode_obj.varnames)
        print('consts:', bytecode_obj.consts)
        print('global', bytecode_obj.names)
        for instr in bytecode_obj:
            print(instr)
        exec(bytecode_obj.to_code(), {'defaultdict': defaultdict})

    def test_man(self):
        import dis
        def innert():
            a = {
                "a": 1,
                "b": "s"
            }
            return  a
        dis.dis(innert)
        # from bytecode import ConcreteBytecode, ConcreteInstr
        # import types
        #
        # cb = ConcreteBytecode()
        #
        # # 变量 a
        # cb.varnames = ["a"]
        # cb.consts = [1, 2, ("a", "b"), None]  # 注意 None 也需要
        # cb.names = []
        # cb.name = "<module>"
        # cb.filename = "<string>"
        # cb.argcount = 0
        # cb.flags = 0
        #
        # cb.extend([
        #     # 加载常量值 1 和 2
        #     ConcreteInstr("LOAD_CONST", 0),  # 1
        #     ConcreteInstr("LOAD_CONST", 1),  # 2
        #
        #     # 构建 value 列表 [1, 2]
        #     ConcreteInstr("BUILD_LIST", 2),
        #
        #     # 加载 keys tuple ("a", "b")
        #     ConcreteInstr("LOAD_CONST", 2),
        #
        #     # 构建 dict {"a": 1, "b": 2}
        #     ConcreteInstr("BUILD_CONST_KEY_MAP", 2),
        #
        #     # 存储到变量 a
        #     ConcreteInstr("STORE_FAST", 0),
        #
        #     # 返回 None
        #     ConcreteInstr("LOAD_CONST", 3),
        #     ConcreteInstr("RETURN_VALUE"),
        # ])
        #
        # # 转换为可执行 code 对象
        # code_obj = cb.to_code()
        #
        # # 创建函数并执行
        # f = types.FunctionType(code_obj, {})
        # f()
