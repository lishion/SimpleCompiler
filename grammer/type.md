我现在正在实现一个类型系统，其特点为:

基本类型如下:
* Int
* String
* Float
* Bool
* Unit

`struct` 定义:
```
struct MyType{
 a: Int,
 b: String
}
```
struct 实例化:
``` 
let instance = {
  a: 1,
  b: "1"
}
```

支持泛型:
```
struct MyType1<T>{
 inner: T
}
```
支持 trait:
```
trait ConvertTo<T>{
    def to() -> T;
}
```
支持泛型方法:
```text
def func<T>(x: T) -> T{
    
}
```
支持类型约束:
```
def func<T: ConvertTo<String>>(x: T){
    
}
```
通过类型约束实现多态，返回实现了 `ConvertTo<String>` trait 的对象:
```
def func<T: ConvertTo<String>>() -> T{
    
}
```
但是我现在遇到一个问题，如果我有以下代码:
```

impl ConvertTo<String> for Int{
    def to() -> String{
        // function body
    }
}

impl ConvertTo<String> for Bool{
    def to() -> String{
        // function body
    }
}

def func<T: ConvertTo<String>>(t: T) -> T{
    return true; // bool 实现了  ConvertTo<String>，所以满足类型约束，应该可以返回
}

let a = func("1"); // 类型推断返回类型为 String，所以 a 类型为 String，但是真正的返回确是一个 bool，出现了冲突
```
以上的问题请问该如何解决，请帮我修改/扩充类型系统来达到消除这种情况。