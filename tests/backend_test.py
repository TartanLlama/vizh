from vizh.ir import *
from vizh.compiler import *
from vizh.linker import *

class BackendTest(object):
    def __init__(self, name):
        self.name = name

    def to_instructions(self, description):
        return [Instruction(*inst) if type(inst) == tuple else Instruction(inst) for inst in description]

    def compile_and_link(self):
        c = Compiler()
        out = c.compile_functions([self.get_function()])[0]
        l = Linker()
        l.link([out], self.name, True)