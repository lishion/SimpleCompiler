from abc import ABC, abstractmethod
from error.exception import *


class LineMaker(ABC):

    @abstractmethod
    def mark(self, start_position, end_position, context: tuple[int, int] = None, context_ast = None) -> str: pass


class SourceCodeMaker(LineMaker):

    def __init__(self, source_code: str):
        self.source_code = source_code
        self.lines = source_code.split("\n")


    def mark(self, start_position: tuple[int, int], end_position: tuple[int, int], context: tuple[int, int] = None, context_ast = None) -> str:
        start_row, start_col = start_position
        end_row, end_col = end_position
        if context:
            scope_start, scope_end = context
        elif context_ast:
            scope_start = context_ast.start_pos[0]
            scope_end = context_ast.end_pos[0]
        else:
            scope_start = max(0, start_row - 2)
            scope_end = min(len(self.lines) - 1, end_row + 2)

        res = []
        line_no_width = len(str(max(scope_end, end_row)))
        for row in range(min(scope_start, start_row),max(scope_end, end_row) + 1):
            line = self.lines[row - 1]
            res.append(str(row + 1))
            res.append("|")
            res.append(line)
            res.append("\n")
            if row < start_row or row > end_row:
                continue
            res.append(" " * (line_no_width + 1))
            for col, char in enumerate(line, start=1):
                if row < start_row or row > end_row:
                    continue
                if (row == start_row) and (col >= start_col) and not (row == end_row and col > end_col):
                   res.append("^")
                elif row == end_row and col <= end_col and not (start_row == end_row):
                    res.append("^")
                elif start_row < row < end_row:
                    res.append("^")
                else:
                    res.append(" ")
            res.append("\n")
        return "".join(res)

class ErrorReporter:
    def __init__(self, line_marker: LineMaker):
        self.line_marker = line_marker
        self.undefined_message = []

    def add_undefined_error_by_ast(self, id_name, node, context_node=None):
        self.undefined_message.append(f"`{id_name}` is not defined\n" + self.line_marker.mark(node.start_pos, node.end_pos, context_ast=context_node))

    def add_undefined_message(self, message, node):
        self.undefined_message.append(f"{message}\n" + self.line_marker.mark(node.start_pos, node.end_pos))

    def report_all(self):
        if self.undefined_message:
            raise UndefinedError("below error found when compile\n" + "\n".join(self.undefined_message))

    def report_undefined(self, id_type, id_name, node, context_node=None):
        raise UndefinedError(f"'{id_name}' is not defined\n" + self.line_marker.mark(node.start_pos, node.end_pos, context_ast=context_node))

    def report_undefined_message(self, message, node, context_node=None):
        raise UndefinedError(f"{message}\n" + self.line_marker.mark(node.start_pos, node.end_pos))

    def mark(self, node, context_node=None) -> str:
        return self.line_marker.mark(node.start_pos, node.end_pos, context_ast=context_node)