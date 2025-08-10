一款从词法分析到语义分析基于 python 实现的编译器，最终代码也编译到 python。纯手工打造。其语法风格类似 python，类型系统借鉴于 Rust。

目前还非常不完善，主要用于体验一下编译器的实现过程。燃尽自己仍无法达到可用的水平。

## Requirements
python 3.12+

## 主要特性
* 静态类型检测
* 基于 Trait 的类型系统
## 基本类型
* Int
* Float
* String
* Bool
* Unit
## 基本语法
```
let x = 1;
struct Point {
    x: Int,
    y: Int,
}
def say_hello(name: String) -> Unit {
    print("Hello, " + name);
}
# this is a comment
```
## Trait
trait 的定义和使用方式类似于 Rust，但是有很多不完善的地方。例如不支持关联类型等。
```
trait Animal {
    def speak() -> String;
}

struct Dog {name: String}
impl Animal for Dog {
    def speak() -> String {
        return "Woof! My name is " + self.name;
    }
}
let my_dog: Dog = Dog{name: "Buddy"};
print(my_dog.speak()); # Woof! My name is Buddy
```
## 运算符重载
支持通过实现特定 Trait 来运算符重载，例如：
* `+`: Add
* `-`: Sub
* `*`: Mul 
* `/` : Div
```
struct Point {
    x: Int,
    y: Int,
}

impl Add for Point {
    def add(self, other: Point) -> Point {
        return Point{x: self.x + other.x, y: self.y + other.y};
    }
}
impl ToString for Point {
    def to_string(self) -> String {
        return "Point{x: " + self.x.to_string() + ", y: " + self.y.to_string() + "}";
    }
}
let p1: Point = Point{x: 1, y: 2};
let p2: Point = Point{x: 3, y: 4};
let p3: Point = p1 + p2; # 使用运算符重载
print(p3.to_string()); # 输出 Point{x: 4, y: 6}

```
## 泛型
```
# 支持泛型，并且会进行编译期展开

def id<T>(a: T) -> T {
    return a;
}

let a = id(1); # 会编译为 id_Int
let b = id(1.5); # 会编译为 add_Float


# 支持 trait 约束
def add<T: Add>(a: T, b: T) -> T {
    return a + b;
}

let a = add(1, 2); # 会编译为add_Int
```
## 条件分支/循环
开发中....