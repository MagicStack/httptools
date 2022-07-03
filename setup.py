import sys

vi = sys.version_info
if vi < (3, 5):
    raise RuntimeError('httptools require Python 3.5 or greater')
else:
    import os.path
    import pathlib

    from setuptools import setup, Extension
    from setuptools.command.build_ext import build_ext as build_ext


CFLAGS = ['-O2']

ROOT = pathlib.Path(__file__).parent

CYTHON_DEPENDENCY = 'Cython(>=0.29.24,<0.30.0)'


class httptools_build_ext(build_ext):
    user_options = build_ext.user_options + [
        ('cython-always', None,
            'run cythonize() even if .c files are present'),
        ('cython-annotate', None,
            'Produce a colorized HTML version of the Cython source.'),
        ('cython-directives=', None,
            'Cythion compiler directives'),
        ('use-system-llhttp', None,
            'Use the system provided llhttp, instead of the bundled one'),
        ('use-system-http-parser', None,
            'Use the system provided http-parser, instead of the bundled one'),
    ]

    boolean_options = build_ext.boolean_options + [
        'cython-always',
        'cython-annotate',
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
        self.cython_always = False
        self.cython_annotate = None
        self.cython_directives = None

    def finalize_options(self):
        # finalize_options() may be called multiple times on the
        # same command object, so make sure not to override previously
        # set options.
        if getattr(self, '_initialized', False):
            return

        need_cythonize = self.cython_always
        cfiles = {}

        for extension in self.distribution.ext_modules:
            for i, sfile in enumerate(extension.sources):
                if sfile.endswith('.pyx'):
                    prefix, ext = os.path.splitext(sfile)
                    cfile = prefix + '.c'

                    if os.path.exists(cfile) and not self.cython_always:
                        extension.sources[i] = cfile
                    else:
                        if os.path.exists(cfile):
                            cfiles[cfile] = os.path.getmtime(cfile)
                        else:
                            cfiles[cfile] = 0
                        need_cythonize = True

        if need_cythonize:
            try:
                import Cython
            except ImportError:
                raise RuntimeError(
                    'please install Cython to compile httptools from source')

            if Cython.__version__ < '0.29':
                raise RuntimeError(
                    'httptools requires Cython version 0.29 or greater')

            from Cython.Build import cythonize

            directives = {}
            if self.cython_directives:
                for directive in self.cython_directives.split(','):
                    k, _, v = directive.partition('=')
                    if v.lower() == 'false':
                        v = False
                    if v.lower() == 'true':
                        v = True

                    directives[k] = v

            self.distribution.ext_modules[:] = cythonize(
                self.distribution.ext_modules,
                compiler_directives=directives,
                annotate=self.cython_annotate)

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


with open(str(ROOT / 'README.md')) as f:
    long_description = f.read()


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
    name='httptools',
    version=VERSION,
    description='A collection of framework independent HTTP protocol utils.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/MagicStack/httptools',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Operating System :: POSIX',
        'Operating System :: MacOS :: MacOS X',
        'Environment :: Web Environment',
        'Development Status :: 5 - Production/Stable',
    ],
    platforms=['macOS', 'POSIX', 'Windows'],
    python_requires='>=3.5.0',
    zip_safe=False,
    author='Yury Selivanov',
    author_email='yury@magic.io',
    license='MIT',
    packages=['httptools', 'httptools.parser'],
    cmdclass={
        'build_ext': httptools_build_ext,
    },
    ext_modules=[
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
    ],
    include_package_data=True,
    test_suite='tests.suite',
    setup_requires=setup_requires,
    extras_require={
        'test': [
            CYTHON_DEPENDENCY
        ]
    }
)
