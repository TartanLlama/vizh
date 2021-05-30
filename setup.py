from distutils.ccompiler import new_compiler 
from setuptools.command.build_py import build_py
from setuptools import setup
from sysconfig import get_paths 
import shutil
import os

build_dir = os.path.join(os.path.dirname(__file__), 'build')

class BuildLibv(build_py): 
    def run(self):
        build_py.run(self)

        c = new_compiler()

        # Compile libv
        libv_objects = c.compile(['libv/io.c'])
        crtv_object = c.compile(['libv/crtv.c'])[0]

        # Create static libv and move crtv.o into the build dir
        output_dir = f'{self.build_lib}/vizh'

        
        if os.name == 'nt':
            shutil.copyfile(crtv_object, f'{output_dir}/crtv.obj')
            c.create_static_lib(libv_objects, 'libv', output_dir=output_dir)
        else:
            shutil.copyfile(crtv_object, f'{output_dir}/crtv.o')
            c.create_static_lib(libv_objects, 'v', output_dir=output_dir)

setup(
    cmdclass={
        'build_py': BuildLibv
    }
)