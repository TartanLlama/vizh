from vizh.ir import *
import vizh.util
import tempfile
import distutils.ccompiler 
import os.path
import sys
import os

libv_decls = []
try:
    # This is generated when the package is built
    # and contains declarations for libv
    import vizh.libv_decls
    libv_decls = vizh.libv_decls.libv_decls
except ImportError:
    # If we're compiling libv itself then it doesn't exist yet
    pass

class CompilerError(Exception):
    pass

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
    def __init__(self, c_compiler=None):
        self.c_compiler = c_compiler or distutils.ccompiler.new_compiler()
        pass

    def emit_prologue(self, function):
        """The prologue sets up the available tapes and read head for the function.

        It looks like this:

        void getA(uint8_t* arg0) {
           uint8_t* static_tapes[1] = {
             arg0
           };
           vizh_tapes_t vizh_tapes;
           vizh_tapes.tapes = static_tapes;
           vizh_tapes.n_tapes = 1;
           vizh_tapes.to_free = NULL;
           vizh_tapes.capacity = 0;
           size_t current_tape = 0;
           uint8_t head_storage = 0;
        """

        return [
            str(function.signature) + ' {',
            f'  uint8_t* static_tapes[{function.signature.n_args}] = {{ ',
            '    ' + ', '.join([f'arg{n}' for n in range(function.signature.n_args)]),
            '  };',
            '  vizh_tapes_t vizh_tapes;',
            '  vizh_tapes.tapes = static_tapes;',
            f'  vizh_tapes.n_tapes = {function.signature.n_args}; ',
            '  vizh_tapes.to_free = NULL;'
            '  vizh_tapes.capacity = 0;',
            '  size_t current_tape = 0;',
            '  uint8_t head_storage = 0;',
        ]
        

    def emit_epilogue(self, function):
        """The epilogue tears down the function, deallocating any leftover tapes.
        """
        return [
            f'  for(size_t i = 0; i < vizh_tapes.n_tapes - {function.signature.n_args}; ++i) {{',
            '    freetape(&vizh_tapes);',
            '  }',
            '}',
        ]

    def emit_instruction(self, instruction, labels, signatures):
        code = []
        if instruction.type == InstructionType.LEFT:
            code = ['  --vizh_tapes.tapes[current_tape];']
        elif instruction.type == InstructionType.RIGHT:
            code = ['  ++vizh_tapes.tapes[current_tape];']
        elif instruction.type == InstructionType.UP:
            code = ['  --current_tape;']
        elif instruction.type == InstructionType.DOWN:
            code = ['  ++current_tape;']
        elif instruction.type == InstructionType.INC:
            code = ['  ++*vizh_tapes.tapes[current_tape];']
        elif instruction.type == InstructionType.DEC:
            code = ['  --*vizh_tapes.tapes[current_tape];']
        elif instruction.type == InstructionType.READ:
            code = ['  head_storage = *vizh_tapes.tapes[current_tape];']
        elif instruction.type == InstructionType.WRITE:
            code = ['  *vizh_tapes.tapes[current_tape] = head_storage;']

        # Loops are implemented by outputting a start label
        # where the LOOP_START instruction is, then checking
        # if the read head is pointing to 0. If it is, then
        # we jump to the end label for this loop.
        elif instruction.type == InstructionType.LOOP_START:
            new_label = labels.generate_label()
            code = [
                f'{new_label}_start:',
                f'  if (*vizh_tapes.tapes[current_tape] == 0) goto {new_label}_end;'
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
            # Creating or destroying tapes requires having access to our tapes
            if instruction.value == 'newtape':
                code = ['  newtape(&vizh_tapes);']
            elif instruction.value == 'freetape':
                code = ['  freetape(&vizh_tapes);']
            else:
                if instruction.value not in signatures:
                    raise CompilerError(f'Unrecognised function call: {instruction.value}')
                callee_signature = signatures[instruction.value]
                code = [f'  {instruction.value}(']
                code += [',\n'.join([f'    vizh_tapes.tapes[current_tape + {arg}]' for arg in range(callee_signature.n_args) ])] 
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

        signature_list = externs + [function.signature for function in functions]
        
        # We need size_t and libv functions
        code = ['#include <stddef.h>',
                '#include "libv.h"']

        # First output forward declarations for all functions and externs
        code += [f'{str(signature)};' for signature in signature_list]

        signature_list += libv_decls
        signatures = {signature.name: signature for signature in signature_list}

        errors = []
        for function in functions:
            try:
                code.append(self.compile_function_to_c(function, signatures))
            except CompilerError as err:
                errors.append((function.signature.name,err))

        if len(errors) > 0:
            messages = [f'Error while compiling {func_name}: {err}' for func_name, err in errors]
            raise CompilerError('\n'.join(messages))
        
        return '\n'.join(code)

    def compile_functions(self, functions, externs=[]):
        code = self.compile_functions_to_c(functions, externs)

        # Write the C code out to a temporary file and compile it 
        # to an object file with the system C compiler.
        c_file_name = None
        with tempfile.NamedTemporaryFile(suffix='.c', mode = "w", delete=False) as c_file:
            c_file.write(code)
            c_file_name = c_file.name

        return self.compile_c_programs([c_file_name], output_dir=os.path.dirname(c_file_name))[0]

    def compile_c_programs(self, file_names, output_dir):
        # If we're compiling the standard library then the libv header is in ./libv, otherwise it's where this file is
        libv_header_path = 'libv' if libv_decls == [] else os.path.dirname(__file__)

        err_log_name = os.path.join(tempfile.gettempdir(), next(tempfile._get_candidate_names()))
        with vizh.util.stdchannel_redirected(sys.stdout, err_log_name) as err_file:
            try:
                opt_args = '/O2' if os.name == 'nt' else '-O3'
                return self.c_compiler.compile(file_names, output_dir, extra_postargs=[opt_args], include_dirs=[libv_header_path])
            except distutils.errors.CompileError:
                err_file.seek(0)
                err_log = err_file.read()
                raise CompilerError(err_log)