"""

trait Show(T){
    def show(self: T) -> String
}

impl Show for Student{
    def show(self: Student) -> String
}

def add(t1: impl (Show + Read), t2: impl Show){

}

a.b.c()

a.b.c

"""