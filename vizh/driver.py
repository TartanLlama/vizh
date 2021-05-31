import click
import vizh.parser
import vizh.linker
import vizh.compiler
import shutil
import tempfile
import sys
import os.path
import cv2

def find_if(l, pred):
    try:
        return next(x for x in l if pred(x))
    except StopIteration:
        return None

def get_file_types(files):
    object_files = []
    c_source_files = []
    vizh_source_files = []

    for file in files:
        if file.endswith('.c'):
            c_source_files.append(file)
        elif file.endswith('.o') or file.endswith('.obj'):
            object_files.append(file)
        else:
            vizh_source_files.append(file)

    return object_files, c_source_files, vizh_source_files

def parse_vizh_files(compiler, files, debug_parser):
    vizh_funcs = []
    had_error = False
    
    with vizh.parser.Parser() as parser:
        for file in files:
            func = parser.parse(file, debug_parser)
            if func:
                vizh_funcs.append(func)
            else:
                had_error = True
    
    if had_error:
        return None
    else:
        return vizh_funcs    

def compile_c_files(compiler, files):
    object_files = []
    had_error = False

    try:
        object_files = compiler.compile_c_programs(files, tempfile.gettempdir())
    except vizh.compiler.CompilerError as err:
        had_error = True
        print(f'C compiler reported an error in compiling {files}:\n{err}', file=sys.stderr)

    if had_error:
        return None
    else: 
        return object_files

def get_default_output_file(compile_only, vizh_functions):
    """Get the default object file, which is:
    - a.exe/a.out if linking an executable,
    - Otherwise:
        - func_name.obj/func_name.o if there is one vizh function
        - Otherwise vizh.o
    """
    if compile_only:
        if len(vizh_functions) == 1:
            if os.name == 'nt':
                return vizh_functions[0].signature.name + '.obj'
            else:
                return vizh_functions[0].signature.name + '.o'
        else:
            return 'vizh.o'
    else:
        return 'a.exe' if os.name == 'nt' else 'a.out'

@click.command()
@click.version_option()
@click.argument('inputs', nargs=-1, type=click.Path(exists=True))
@click.option('-c', '--compile-only', 'compile_only', is_flag=True, help="Only compile, don't link.")
@click.option('-o', '--output-file', 'output_file', type=click.Path(), default=None, help="Output file for executables or vizh object files.")
@click.option('-q', '--quiet', is_flag=True, help="Suppress output.")
@click.option('--debug-parser', 'debug_parser', is_flag=True, help="Display how the parser understands your source file.")
def entry(inputs, compile_only, output_file, quiet, debug_parser):
    supplied_object_files, c_source_files, vizh_source_files = get_file_types(inputs)
    compiler = vizh.compiler.Compiler()
    
    vizh_funcs = parse_vizh_files(compiler, vizh_source_files, debug_parser)
    vizh_object_file = compiler.compile_functions(vizh_funcs) if vizh_funcs else None

    c_object_files = compile_c_files(compiler, c_source_files)
    
    compilation_failed = vizh_object_file == None or c_object_files == None

    output_file = output_file or get_default_output_file(compile_only, vizh_funcs)
       
    # If we're only compiling, move the compiled object files into the current directory and exit
    if compile_only:
        if vizh_object_file:
            shutil.move(vizh_object_file, output_file)
        for file in c_object_files:
            shutil.move(file, os.path.join(os.getcwd(), os.path.basename(file)))
        if not quiet:
            if vizh_object_file:
                print(vizh_source_files, '->', output_file)
            for (source,object) in zip(c_source_files, c_object_files):
                print(source, '->', os.path.basename(object), file=sys.stdout)
        if compilation_failed:
            print("Compilation failed :(", file=sys.stderr)
            return -1
        else:
            return 0

    if compilation_failed:
        print("Compilation failed :(", file=sys.stderr)
        return -1

    object_files = supplied_object_files + c_object_files + [vizh_object_file]
    linker = vizh.linker.Linker()
    link_crtv = find_if(vizh_funcs, lambda f: f.signature.name == 'vizh_main') != None

    try:
        linker.link(object_files, output_file, link_crtv)

        if not quiet:
            print(vizh_source_files + c_source_files + supplied_object_files, '->', output_file)
    except vizh.linker.LinkerError as err:
            print(f'C compiler reported an error in linking:\n{err}', file=sys.stderr)

if __name__ == '__main__':
    entry()