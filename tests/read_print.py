from vizh.ir import *
import tests.backend_test

class ReadPrint(tests.backend_test.BackendTest):
    def __init__(self):
        super().__init__("read_print")

    def get_function(self):
        return Function(FunctionSignature("main", 1, False), self.to_instructions([
            (InstructionType.CALL, "readin"),
            InstructionType.INC,
            (InstructionType.CALL, "print") 
        ]))

