import distutils.ccompiler
import os.path
import os
import vizh.util
import sys
import tempfile

LIBV_NAME = 'libv.lib' if os.name == 'nt' else 'libv.a'
CRTV_NAME = 'crtv.obj' if os.name == 'nt' else 'crtv.o'

class LinkerError(Exception):
    pass

class Linker(object):
    def __init__(self, c_compiler=None):
        self.c_compiler = c_compiler or distutils.ccompiler.new_compiler()

    def link(self, object_files, output_name, link_crtv=True):
        """Links the given object files into an executable with the given name.

        link_crtv specifies whether to link crtv.o, which defines main
        """

        # libv.a and crtv.o are installed in the same directory as this file
        vizh_path = os.path.dirname(__file__)
        object_files.append(os.path.join(vizh_path, LIBV_NAME))
        if link_crtv:
            object_files.append(os.path.join(vizh_path, CRTV_NAME))

        err_log_name = os.path.join(tempfile.gettempdir(), next(tempfile._get_candidate_names()))
        with vizh.util.stdchannel_redirected(sys.stdout, err_log_name) as err_file:
            try:
                return self.c_compiler.link(self.c_compiler.EXECUTABLE, object_files, output_name)
            except distutils.errors.LinkError:
                err_file.seek(0)
                err_log = err_file.read()
                raise LinkerError(err_log)
