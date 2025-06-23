当有泛型存在时，创建 vtable 的逻辑要复杂很多。如果没有泛型，那么在遍历到 trait impl 时将函数实现放入 global vtable 中，例如
```text
trait Read{
    def to() -> String;
}

impl MyType for Read{
    def to() -> String{
        # some impl logic
    }
}
```
这个时候，可以放入全局 vtable:
```
{
 MyType: {
    to: function impl code
 }
}
```
当创建一个 MyType 的实例的时候，从全局 vtable 取出所有函数放入实例中，例如:
```text
let my = MyType{item: 1};
```
实际上在内存可能表示为:
```
let my = {
data: {item: 1},
vtable: {to: function impl code}
}
```
但是一旦引入泛型这个事情就变得比较棘手，比如:
```text
trait Convert<T>{
    def into() -> T;
}

impl MyType<T>{a: T};

impl MyType<T> for Convert<T>{

}

def test_convert<T>(t: T) -> dyn Convert<T>{
    let mytype1 = MyType{a: t}; #1. 此时 MyType 的类型尚未决定，是 MyType<T>
    let b = mytype1.into();

    return MyType{
        a: t
    }
}

let c = test_convert("1"); #2 通过类型推断可以得出 MyType 实际参数为 MyType<String>
```
可以看出了，在注释 #1 时候还无法最 MyType 的最终类型进行确定，因此无法决定需要拿 global 中的哪个 vtable 来填充实例的 
vtable。必须等到 #2 的调用推断出了类型，才能确定需要的是 MyType<String> 的 vtable。此时需要**重新遍历函数体，替换所有类型变量**。

因此，当一个实例被创建的时候无法对其 vtable 进行填充，而是要等到类型被确认的时候才能进行。

在泛型存在的情况下，vtable 的 key 还需要加上具体的类型参数的信息，比如从:
```
{
 MyType: {
    to: function impl code
 }
}
```
改为:
```
{
 MyType<String>: {
    to: function impl code
 }
}
```