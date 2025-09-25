import sys

from Cython.Build import cythonize

vi = sys.version_info
if vi < (3, 8):
    raise RuntimeError('httptools require Python 3.8 or greater')
else:
    import os.path
    import pathlib

    from setuptools import setup, Extension
    from setuptools.command.build_ext import build_ext as build_ext


CFLAGS = ['-O2']

ROOT = pathlib.Path(__file__).parent

CYTHON_DEPENDENCY = 'Cython>=3.1.0'


class httptools_build_ext(build_ext):
    user_options = build_ext.user_options + [
        ('use-system-llhttp', None,
            'Use the system provided llhttp, instead of the bundled one'),
        ('use-system-http-parser', None,
            'Use the system provided http-parser, instead of the bundled one'),
    ]

    boolean_options = build_ext.boolean_options + [
        'use-system-llhttp',
        'use-system-http-parser',
    ]

    def initialize_options(self):
        # initialize_options() may be called multiple times on the
        # same command object, so make sure not to override previously
        # set options.
        if getattr(self, '_initialized', False):
            return

        super().initialize_options()
        self.use_system_llhttp = False
        self.use_system_http_parser = False

    def finalize_options(self):
        # finalize_options() may be called multiple times on the
        # same command object, so make sure not to override previously
        # set options.
        if getattr(self, '_initialized', False):
            return

        super().finalize_options()

        self._initialized = True

    def build_extensions(self):
        mod_parser, mod_url_parser = self.distribution.ext_modules
        if self.use_system_llhttp:
            mod_parser.libraries.append('llhttp')

            if sys.platform == 'darwin' and \
                    os.path.exists('/opt/local/include'):
                # Support macports on Mac OS X.
                mod_parser.include_dirs.append('/opt/local/include')
        else:
            mod_parser.include_dirs.append(
                str(ROOT / 'vendor' / 'llhttp' / 'include'))
            mod_parser.include_dirs.append(
                str(ROOT / 'vendor' / 'llhttp' / 'src'))
            mod_parser.sources.append('vendor/llhttp/src/api.c')
            mod_parser.sources.append('vendor/llhttp/src/http.c')
            mod_parser.sources.append('vendor/llhttp/src/llhttp.c')

        if self.use_system_http_parser:
            mod_url_parser.libraries.append('http_parser')

            if sys.platform == 'darwin' and \
                    os.path.exists('/opt/local/include'):
                # Support macports on Mac OS X.
                mod_url_parser.include_dirs.append('/opt/local/include')
        else:
            mod_url_parser.include_dirs.append(
                str(ROOT / 'vendor' / 'http-parser'))
            mod_url_parser.sources.append(
                'vendor/http-parser/http_parser.c')

        super().build_extensions()


with open(str(ROOT / 'httptools' / '_version.py')) as f:
    for line in f:
        if line.startswith('__version__ ='):
            _, _, version = line.partition('=')
            VERSION = version.strip(" \n'\"")
            break
    else:
        raise RuntimeError(
            'unable to read the version from httptools/_version.py')


setup_requires = []

if (not (ROOT / 'httptools' / 'parser' / 'parser.c').exists() or
        '--cython-always' in sys.argv):
    # No Cython output, require Cython to build.
    setup_requires.append(CYTHON_DEPENDENCY)


setup(
    version=VERSION,
    platforms=['macOS', 'POSIX', 'Windows'],
    zip_safe=False,
    packages=['httptools', 'httptools.parser'],
    cmdclass={
        'build_ext': httptools_build_ext,
    },
    ext_modules=cythonize([
        Extension(
            "httptools.parser.parser",
            sources=[
                "httptools/parser/parser.pyx",
            ],
            extra_compile_args=CFLAGS,
        ),
        Extension(
            "httptools.parser.url_parser",
            sources=[
                "httptools/parser/url_parser.pyx",
            ],
            extra_compile_args=CFLAGS,
        ),
    ]),
    include_package_data=True,
    exclude_package_data={"": ["*.c", "*.h"]},
    test_suite='tests.suite',
    setup_requires=setup_requires,
    extras_require={
        'test': [
            CYTHON_DEPENDENCY
        ]
    }
)
