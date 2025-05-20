
class SyntaxError(Exception):
    """Exception raised for syntax errors in the code."""
    def __init__(self, message):
        super().__init__(message)



class UndefinedError(Exception):
    def __init__(self, message):
        super().__init__(message)

class TypeError(Exception):
    def __init__(self, message):
        super().__init__(message)

class DuplicateDefineError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class TypeConstraintError(Exception):
    def __init__(self, message):
        super().__init__(message)