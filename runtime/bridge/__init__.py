BRIDGE_CODE = """

trait Add{
    def add(rhs: Self) -> Self;
}

trait Sub{
    def sub(rhs: Self) -> Self;
}

trait Mul{
    def mul(rhs: Self) -> Self;
}

trait Div{
    def div(rhs: Self) -> Self;
}

trait Compare{
  def gt(rhs: Self) -> Bool;
  def eq(rhs: Self) -> Bool;
  def lt(rhs: Self) -> Bool;
  def gte(rhs: Self) -> Bool;
  def lte(rhs: Self) -> Bool;
}


impl Compare for Int {
  def gt(rhs: Self) -> Bool{
    return gt_int(self, rhs);
  }
  
  def gte(rhs: Self) -> Bool{
    return logic_or(
        gt_int(self, rhs),
        eq_int(self, rhs)
    );
  }
  
  def lt(rhs: Self) -> Bool{
    return lt_int(self, rhs);
  }
  
  def lte(rhs: Self) -> Bool{
      return logic_or(
        lt_int(self, rhs),
        eq_int(self, rhs)
    );
  }
  
  def eq(rhs: Self) -> Bool{
    return eq_int(self, rhs);
  }
}

impl Add for Int {
    def add(rhs: Self) -> Self {
        return add_int(self, rhs);
    }
}

impl Sub for Int {
    def sub(rhs: Self) -> Self {
        return sub_int(self, rhs);
    }
}

impl Div for Int {
    def div(rhs: Self) -> Self {
        return div_int(self, rhs);
    }
}

impl Mul for Int {
    def mul(rhs: Self) -> Self {
        return mul_int(self, rhs);
    }
}


impl Add for Float {
    def add(rhs: Self) -> Self {
        return add_float(self, rhs);
    }
}

impl Sub for Float {
    def sub(rhs: Self) -> Self {
        return sub_float(self, rhs);
    }
}

impl Div for Float {
    def div(rhs: Self) -> Self {
        return div_float(self, rhs);
    }
}

impl Mul for Float {
    def mul(rhs: Self) -> Self {
        return mul_float(self, rhs);
    }
}

impl Add for String {
    def add(rhs: Self) -> Self {
        return add_string(self, rhs);
    }
}


 

trait ToString {
    def to_string() -> String;
}


impl ToString for String {
    def to_string() -> String {
        return self;
    }
}

impl ToString for Int {
    def to_string() -> String {
        return int_to_string(self);
    }
}

impl ToString for Float {
    def to_string() -> String {
        return float_to_string(self);
    }
}

impl ToString for Bool {
    def to_string() -> String {
        return bool_to_string(self);
    }
}

def print(t: impl ToString) -> Unit {
    echo(t.to_string());
}

impl Compare for Float {
  def gt(rhs: Self) -> Bool{
    return gt_float(self, rhs);
  }
  
  def gte(rhs: Self) -> Bool{
    return logic_or(
        gt_float(self, rhs),
        eq_float(self, rhs)
    );
  }
  
  def lt(rhs: Self) -> Bool{
    return lt_float(self, rhs);
  }
  
  def lte(rhs: Self) -> Bool{
      return logic_or(
        lt_float(self, rhs),
        eq_float(self, rhs)
    );
  }
  
  def eq(rhs: Self) -> Bool{
    return eq_float(self, rhs);
  }
}

impl Compare for String {
  def gt(rhs: Self) -> Bool{
    return gt_string(self, rhs);
  }
  
  def gte(rhs: Self) -> Bool{
    return logic_or(
        gt_string(self, rhs),
        eq_string(self, rhs)
    );
  }
  
  def lt(rhs: Self) -> Bool{
    return lt_string(self, rhs);
  }
  
  def lte(rhs: Self) -> Bool{
      return logic_or(
        lt_string(self, rhs),
        eq_string(self, rhs)
    );
  }
  
  def eq(rhs: Self) -> Bool{
    return eq_string(self, rhs);
  }
}

# impl Compare for Bool {
#   def gt(rhs: Self) -> Bool{
#     return gt_bool(self, rhs);
#   }
#   
#   def gte(rhs: Self) -> Bool{
#     return logic_or(
#         gt_bool(self, rhs),
#         eq_bool(self, rhs)
#     );
#   }
#   
#   def lt(rhs: Self) -> Bool{
#     return lt_bool(self, rhs);
#   }
#   
#   def lte(rhs: Self) -> Bool{
#       return logic_or(
#         lt_bool(self, rhs),
#         eq_bool(self, rhs)
#     );
#   }
#   
#   def eq(rhs: Self) -> Bool{
#     return eq_bool(self, rhs);
#   }
# }
"""