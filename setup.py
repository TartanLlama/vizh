from distutils.ccompiler import new_compiler 
from setuptools.command.build_py import build_py
from setuptools import setup
from sysconfig import get_paths 
import shutil
import os
import sys

# We're going to use the package we're installing
# to compile its own standard library.
# Disgusting.
sys.path = ['.'] + sys.path
import vizh.libv
sys.path = sys.path[1:]

build_dir = os.path.join(os.path.dirname(__file__), 'build')

class BuildLibv(build_py): 
    def run(self):
        build_py.run(self)

        output_dir = f'{self.build_lib}/vizh'
        vizh.libv.compile_libv('libv', output_dir)

setup(
    cmdclass={
        'build_py': BuildLibv
    }
)