from vizh.ir import *
import tests.backend_test

class Memcopy(tests.backend_test.BackendTest):
    def __init__(self):
        super().__init__("memcopy")

    def get_function(self):
        return Function(FunctionSignature("memcopy", 3, False), self.to_instructions([
            InstructionType.LOOP_START,
            InstructionType.DOWN,
            InstructionType.READ,
            InstructionType.DOWN,
            InstructionType.WRITE,
            InstructionType.RIGHT,
            InstructionType.UP,
            InstructionType.RIGHT,
            InstructionType.UP,
            InstructionType.DEC,
            InstructionType.LOOP_END
        ]))

