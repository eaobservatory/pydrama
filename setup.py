#!/local/python3/bin/python3

from jac_sw import uae
import numpy
import time
import socket

uae.git_version_file('drama/version.py')

uae.setup(
    packages = ['drama'],
    ext_modules = [
        uae.Extension("drama.__drama__", ["src/drama.pyx"],
            depends=['setup.py',
                     'src/drama.pxd',
                     'src/ditsaltin.h',
                     'src/ditsmsg.h'],
            include_dirs=uae.incs + [numpy.get_include()],
            library_dirs=uae.libs,
            libraries=['jit', 'expat', 'tide', 'ca', 'Com', 'git',
                       'dul', 'dits', 'imp', 'sds', 'ers', 'mess', 'm'],
            define_macros=[("unix",None),("DPOSIX_1",None),
                           ("_GNU_SOURCE",None),("UNIX",None)],
            # preserve wrapped functions for debugging/profiling
            extra_compile_args=["-fno-inline-functions-called-once",
                                "-Wno-unreachable-code"]
        )]
)
