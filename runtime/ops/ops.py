OPS_CODE = """
trait Ops{
  def add(rhs: Self) -> Self;
  def sub(rhs: Self) -> Self;
  def mul(rhs: Self) -> Self;
  def div(rhs: Self) -> Self;
}

impl Ops for Int {
  def add(rhs: Self) -> Self {
    return add_int(self, rhs);
  }

  def sub(rhs: Self) -> Self {
    return sub_int(self, rhs);
  }

  def mul(rhs: Self) -> Self {
    return mul_int(self, rhs);
  }

  def div(rhs: Self) -> Self {
    return div_int(self, rhs);
  }
}


impl Ops for Float {
  def add(rhs: Self) -> Self {
    return add_float(self, rhs);
  }

  def sub(rhs: Self) -> Self {
    return sub_float(self, rhs);
  }

  def mul(rhs: Self) -> Self {
    return mul_float(self, rhs);
  }

  def div(rhs: Self) -> Self {
    return div_float(self, rhs);
  }
}
"""