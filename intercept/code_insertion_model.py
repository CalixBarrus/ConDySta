from typing import List


class CodeInsertionModel:
    """
    Bare bones model class containing necessary information for a given code insertion
    """
    code_to_insert: str
    method_index: int
    line_number: int
    registers: List[str]

    def __init__(self, code_to_insert, method_index, line_number, registers):
        self.code_to_insert = code_to_insert
        self.method_index = method_index
        self.line_number = line_number
        self.registers = registers