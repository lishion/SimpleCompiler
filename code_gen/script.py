from typing import List
class PythonCodeGenerator:
    def __init__(self):
        self._indent_size = 0
        self._codes = []

    def __enter__(self):
        self.indent()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.dedent()

    def indent(self):
        self._indent_size = self._indent_size + 1

    def dedent(self):
        self._indent_size = self._indent_size - 1

    def make_indent(self, strings: callable) -> str:
        self.indent()
        strings = strings()
        if isinstance(strings, str):
            strings = strings.split("\n")
        res = "\n".join([f"{'    ' * self._indent_size}{s}" for s in strings])
        self.dedent()
        return res

    def add_code(self, code: str|List[str]):
        self._codes.append('    ' * self._indent_size + code)

    def __iadd__(self, code: str|List[str]) -> "Indent":
        self.add_code(code)
        return self

    @property
    def codes(self) -> List[str]:
        return self._codes
