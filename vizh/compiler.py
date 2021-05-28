from vizh.ir import *
import tempfile
import distutils.ccompiler 
import os.path

# Signatures for functions defined in libv.a
LIBV_EXTERNS = [
    FunctionSignature("putstr", 1, False)
]

class Labels(object):
    """Keeps track of the stack of labels generated for a given function"""
    def __init__(self):
        self.stack = []
        self.current_label = 0

    def generate_label(self):
        new_label = f'label{self.current_label}'
        self.stack.append(new_label)
        self.current_label += 1
        return new_label

    def pop_label(self):
        return self.stack.pop()

class Compiler(object):
    def __init__(self):
        pass

    def emit_prologue(self, function):
        """The prologue sets up the available tapes and read head for the function.

        It looks like this:

        void function_name (char* arg0, char* arg1) {
            char* tapes[1] = {
                arg0, arg1
            };
            size_t current_tape = 0;
            char head_storage = 0;
        """

        code = []
        code.append(str(function.signature) + ' {')
        code.append(f'  char* tapes[{function.signature.n_args}] = {{')
        code.append('    ' + ', '.join([f'arg{n}' for n in range(function.signature.n_args)]))
        code.append('  };')
        code.append('  size_t current_tape = 0;')
        code.append('  char head_storage = 0;')
        return code

    def emit_epilogue(self, function):
        """The epilogue tears down the function.

        Currently it does nothing, but this should handle returning tapes and 
        deallocating any additional tapes allocated in this function.
        """
        return ['}']

    def emit_instruction(self, instruction, labels, signatures):
        code = []
        if instruction.type == InstructionType.LEFT:
            code = ['  --tapes[current_tape];']
        elif instruction.type == InstructionType.RIGHT:
            code = ['  ++tapes[current_tape];']
        elif instruction.type == InstructionType.UP:
            code = ['  --current_tape;']
        elif instruction.type == InstructionType.DOWN:
            code = ['  ++current_tape;']
        elif instruction.type == InstructionType.INC:
            code = ['  ++*tapes[current_tape];']
        elif instruction.type == InstructionType.DEC:
            code = ['  --*tapes[current_tape];']
        elif instruction.type == InstructionType.READ:
            code = ['  head_storage = *tapes[current_tape];']
        elif instruction.type == InstructionType.WRITE:
            code = ['  *tapes[current_tape] = head_storage;']

        # Loops are implemented by outputting a start label
        # where the LOOP_START instruction is, then checking
        # if the read head is pointing to 0. If it is, then
        # we jump to the end label for this loop.
        elif instruction.type == InstructionType.LOOP_START:
            new_label = labels.generate_label()
            code = [
                f'{new_label}_start:',
                f'  if (*tapes[current_tape] == 0) goto {new_label}_end;'
            ]
        elif instruction.type == InstructionType.LOOP_END:
            label = labels.pop_label()
            code = [
                f'  goto {label}_start;',
                f'{label}_end: ;'
            ]

        # Function calls will fulfil arguments from the tape which
        # is currently active.
        elif instruction.type == InstructionType.CALL:
            callee_signature = signatures[instruction.value]
            code = [f'  {instruction.value}(']
            code += [f'    tapes[current_tape + {arg}]' for arg in range(callee_signature.n_args) ] 
            code += ['  );']

        return (code, labels)
        
    def compile_function_to_c(self, function, signatures):
        """Compiles the given IR to C.
        
        Any functions which are called from this function
        must be present in signatures so that the code generator
        knows how many arguments to pass."""

        code = []
        code += self.emit_prologue(function)
        labels = Labels()
        for instruction in function.instructions:
            (new_code, new_labels) = self.emit_instruction(instruction, labels, signatures)
            code += new_code
            labels = new_labels
        code += self.emit_epilogue(function)
        return '\n'.join(code)

    def compile_functions_to_c(self, functions, externs=[]):
        """Compiles the given IR functions to C.
        
        Any functions which are called by these functions and
        are not present (i.e. they'll be linked against later)
        must have their signatures passed as externs.
        """
        # Mangle main function: real main is provided by libv
        for function in functions:
            if function.signature.name == "main":
                function.signature.name = "vizh_main"

        signature_list = LIBV_EXTERNS + externs + [function.signature for function in functions]
        signatures = {signature.name: signature for signature in signature_list}
        
        # We need size_t
        code = ['#include <stddef.h>']

        # First output forward declarations for all functions and externs (including libv)
        code += [f'{str(signature)};' for signature in signature_list]

        code += [self.compile_function_to_c(function, signatures) for function in functions]
        
        return '\n'.join(code)

    def compile_functions(self, functions, externs=[]):
        code = self.compile_functions_to_c(functions, externs)

        # Write the C code out to a temporary file and compile it 
        # to an object file with the system C compiler.
        with tempfile.NamedTemporaryFile(suffix='.c', mode = "w") as c_file:
            c_file.write(code)
            c_file.flush()
            c_compiler = distutils.ccompiler.new_compiler()
            o_file = c_compiler.compile([c_file.name], output_dir=os.path.dirname(c_file.name))
            return o_file
