import distutils.ccompiler
import os.path
import os

LIBV_NAME = 'libv.lib' if os.name == 'nt' else 'libv.a'
CRTV_NAME = 'crtv.obj' if os.name == 'nt' else 'crtv.o'

class Linker(object):
    def __init__(self):
        pass

    def link(self, object_files, output_name, link_crtv=True):
        """Links the given object files into an executable with the given name.

        link_crtv specifies whether to link crtv.o, which defines main
        """

        c_compiler = distutils.ccompiler.new_compiler()

        # libv.a and crtv.o are installed in the same directory as this file
        vizh_path = os.path.dirname(__file__)
        object_files.append(os.path.join(vizh_path, LIBV_NAME))
        if link_crtv:
            object_files.append(os.path.join(vizh_path, CRTV_NAME))

        c_compiler.link(c_compiler.EXECUTABLE, object_files, output_name)