from vizh.ir import *
import tests.backend_test

class HelloPutstr(tests.backend_test.BackendTest):
    def __init__(self):
        super().__init__("putstr")

    def get_function(self):
        return Function(FunctionSignature("main", 1, False), self.to_instructions(
            [InstructionType.INC]*72 +
            [InstructionType.READ, 
            InstructionType.RIGHT,
            InstructionType.WRITE] +
            [InstructionType.INC]*29 +
            [InstructionType.READ, 
            InstructionType.RIGHT,
            InstructionType.WRITE] +
            [InstructionType.INC]*7 +
            [InstructionType.READ, 
            InstructionType.RIGHT,
            InstructionType.WRITE,
            InstructionType.RIGHT,
            InstructionType.WRITE] +
            [InstructionType.INC]*3 +
            [InstructionType.LEFT] * 4 +
            [(InstructionType.CALL, "putstr")]))
