import vizh.compiler
import vizh.parser
import vizh.ir
import glob
import os.path
import re
import distutils.ccompiler
import shutil
import tempfile

LIBV_HEADER_NAME = 'libv.h'
LIBV_VIZH_HEADER_NAME = 'libv_vizh.h'
LIBV_PYTHON_IMPORT_NAME = 'libv_decls.py'

def find_libv_files(path):
    c_files = []
    vizh_files = []
    crtv_file = None

    for file in glob.glob(path + '/**', recursive=True):
        if file.endswith('.c'):
            if file.endswith('crtv.c'):
                crtv_file = file
            else:
                c_files.append(file)
        elif file.endswith('.png'):
            vizh_files.append(file)

    return c_files, vizh_files, crtv_file

#WHEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE
cdecl_regex = re.compile("^void ([a-zA-Z0-9]+)\(((?:uint8_t\*(?: [a-zA-Z0-9]+)?(?:, )?)*)\);$")
def parse_c_declaration(decl):
    #PARSING C WITH REGEX LIKE A HEATHEN
    #This is actually somewhat reasonable because libv functions only return void and take uint8_t*s

    groups = re.match(cdecl_regex, decl)
    if not groups:
        return None
    function_name = groups[1]
    n_args = groups[2].count('uint8_t*')
    return vizh.ir.FunctionSignature(function_name, n_args)

def parse_vizh_files(files):
    vizh_funcs = []
    with vizh.parser.Parser() as parser:
        for file in files:
            vizh_funcs.append(parser.parse(file))
    return vizh_funcs

def write_libv_vizh_header(vizh_funcs, output_dir):
    """Write a C header with the declarations of the libv functions written in vizh"""
    libv_vizh_header = '#include <stdint.h>\n'
    libv_vizh_header += '\n'.join([str(func.signature)+';' for func in vizh_funcs])
    with open(os.path.join(output_dir, LIBV_VIZH_HEADER_NAME), 'w') as header_file:
        header_file.write(libv_vizh_header) 

def parse_libv_c_decls(libv_source_path):
    """Parse the declarations of libv functions written in C and turn them into FunctionSignatures"""
    libv_c_decls = []
    libv_header_path = os.path.join(libv_source_path, LIBV_HEADER_NAME)
    with open(libv_header_path, 'r') as libv_header:
        #First line is an include
        for line in libv_header.readlines()[1:]:
            decl = parse_c_declaration(line)
            if decl:
                libv_c_decls.append(decl)
    return libv_c_decls

def generate_libv_python_decls(vizh_funcs, libv_c_decls, output_dir):
    libv_python_imports = 'from vizh.ir import FunctionSignature\n'
    libv_python_imports += 'libv_decls = [\n\t'
    libv_python_imports += ',\n\t'.join([repr(func.signature) for func in vizh_funcs])
    libv_python_imports += ',\n\t'
    libv_python_imports += ',\n\t'.join([repr(signature) for signature in libv_c_decls])
    libv_python_imports += '\n]\n'
    with open(os.path.join(output_dir, LIBV_PYTHON_IMPORT_NAME), 'w') as header_file:
        header_file.write(libv_python_imports)  

def compile_libv(libv_source_path, output_dir):
    c_files, vizh_files, crtv_file = find_libv_files(libv_source_path)

    c = vizh.compiler.Compiler()
    
    libv_objects = c.compile_c_programs(c_files, tempfile.gettempdir())
    crtv_object = c.compile_c_programs([crtv_file], tempfile.gettempdir())[0]
    vizh_funcs = parse_vizh_files(vizh_files)

    write_libv_vizh_header(vizh_funcs, output_dir) 
    libv_c_decls = parse_libv_c_decls(libv_source_path)

    shutil.copyfile(os.path.join(libv_source_path, LIBV_HEADER_NAME), os.path.join(output_dir, LIBV_HEADER_NAME))

    generate_libv_python_decls(vizh_funcs, libv_c_decls, output_dir)

    libv_objects.append(c.compile_functions(vizh_funcs, libv_c_decls))
    
    # Create static libv and move crtv.o into the build dir
    linker = c.c_compiler
        
    if os.name == 'nt':
        shutil.copyfile(crtv_object, f'{output_dir}/crtv.obj')
        linker.create_static_lib(libv_objects, 'libv', output_dir=output_dir)
    else:
        shutil.copyfile(crtv_object, f'{output_dir}/crtv.o')
        linker.create_static_lib(libv_objects, 'v', output_dir=output_dir)