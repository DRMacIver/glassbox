from distutils.core import setup
from setuptools import find_packages
import os
import platform
from distutils.core import Extension
from distutils import errors
import sys
from distutils.command.build_ext import build_ext
from setuptools.command.sdist import sdist as _sdist


try:
    from Cython.Distutils import build_ext as cython_build_ext
except ImportError:
    use_cython = False
else:
    use_cython = True


def local_file(name):
    return os.path.relpath(os.path.join(os.path.dirname(__file__), name))

SOURCE = local_file("src")
README = local_file("README.rst")

setup_args = dict(
    name='glassbox',
    version="0.1.0",
    author='David R. MacIver',
    author_email='david@drmaciver.com',
    packages=find_packages(SOURCE),
    package_dir={"": SOURCE},
    url='https://github.com/DRMacIver/hypothesis',
    long_description=open("README.rst").read(),
    license='MPL v2',
    description='A library for introspecting program state',
    zip_safe=True,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Operating System :: Unix",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Software Development :: Testing",
    ],
    tests_require=['pytest', 'coverage'],
    cmdclass={},
)


ext_errors = (
    errors.CCompilerError,
    errors.DistutilsExecError,
    errors.DistutilsPlatformError,
)


class BuildFailed(Exception):
    """Raise this to indicate the C extension wouldn't build."""
    def __init__(self):
        Exception.__init__(self)
        self.cause = sys.exc_info()[1]


class ve_build_ext(build_ext):
    """Build C extensions, but fail with a straightforward exception."""

    def run(self):
        """Wrap `run` with `BuildFailed`."""
        try:
            build_ext.run(self)
        except errors.DistutilsPlatformError:
            raise BuildFailed()

    def build_extension(self, ext):
        """Wrap `build_extension` with `BuildFailed`."""
        try:
            # Uncomment to test compile failure handling:
            #   raise errors.CCompilerError("OOPS")
            build_ext.build_extension(self, ext)
        except ext_errors:
            raise BuildFailed()
        except ValueError as err:
            # this can happen on Windows 64 bit, see Python issue 7511
            if "'path'" in str(err):    # works with both py 2/3
                raise BuildFailed()
            raise

CYTHON_FILE = "src/glassbox/extension.pyx"


class sdist(_sdist):
    def run(self):
        from Cython.Build import cythonize
        cythonize([CYTHON_FILE])
        _sdist.run(self)
setup_args['cmdclass']['sdist'] = sdist


if (
    platform.python_implementation() == 'CPython'
):

    if use_cython:
        extension = Extension(
            "glassbox.extension",
            sources=[CYTHON_FILE],
        )
        setup_args['cmdclass']['build_ext'] = cython_build_ext
    else:
        extension = Extension(
            "glassbox.extension",
            sources=[CYTHON_FILE.replace('.pyx', '.c')],
        )
        setup_args['cmdclass']['build_ext'] = ve_build_ext

    setup_args['ext_modules'] = [extension]


def main():
    """Actually invoke setup() with the arguments we built above."""
    # For a variety of reasons, it might not be possible to install the C
    # extension.  Try it with, and if it fails, try it without.
    try:
        setup(**setup_args)
    except BuildFailed as exc:
        msg = "Couldn't install with extension module, trying without it..."
        exc_msg = "%s: %s" % (exc.__class__.__name__, exc.cause)
        print("**\n** %s\n** %s\n**" % (msg, exc_msg))

        del setup_args['ext_modules']
        setup(**setup_args)

if __name__ == '__main__':
    main()
