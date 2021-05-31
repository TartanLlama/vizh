from enum import Enum, auto

class InstructionType(Enum):
    """All the instructions available in vizh"""
    LEFT = auto()
    RIGHT = auto()
    UP = auto()
    DOWN = auto()
    INC = auto()
    DEC = auto()
    READ = auto()
    WRITE = auto()
    LOOP_START = auto()
    LOOP_END = auto()
    CALL = auto()


class Instruction(object):
    """An instruction has a type and potentially a value
    Currently only the call instruction can have a value
    """
    def __init__(self, type, value=None):
        self.type = type
        self.value = value

    def __str__(self):
        """Turns instruction into '<instruction type> (<value>);'

        Examples:
            LOOP_START;
            CALL(hello_world);
        """
        ret = str(self.type)[len('InstructionType.'):]
        if self.value:
            ret += f'({self.value})'
        ret += ';'
        return ret

class FunctionSignature(object):
    """Represents the signature of a function:
    Its name andhow many tape arguments it takes
    """

    def __init__(self, name, n_args):
        self.name = name
        self.n_args = n_args

    def __str__(self):
        """Turns the signature into the equivalent C function signature"""
        arguments = ', '.join([f'uint8_t* arg{n}' for n in range(self.n_args)])
        return f'void {self.name} ({arguments})'

    def __repr__(self):
        return f'FunctionSignature("{self.name}", {self.n_args})'

class Function(object):
    def __init__(self, signature, instructions):
        self.signature = signature
        self.instructions = instructions

    def __str__(self):
        """Turns function into:
        <return type> <name> (<arguments>) {
            <instructions>*
        }

        Example:
            void call_hello () {
                CALL(hello);
            }
        """
        ret = f'{self.signature} {{'
        for instr in self.instructions:
            ret += f'\n\t{instr}'
        ret += '\n}'
        return ret
    