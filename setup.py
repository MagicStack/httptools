from setuptools import setup, Extension


setup(
    name='httptools',
    version='0.0.7',
    description='A collection of framework independent HTTP protocol utils.',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Operating System :: POSIX',
        'Operating System :: MacOS :: MacOS X',
        'Environment :: Web Environment',
        'Development Status :: 4 - Beta',
    ],
    platforms=['POSIX'],
    author='Yury Selivanov',
    author_email='yury@magic.io',
    license='MIT',
    packages=['httptools', 'httptools.parser'],
    ext_modules=[
        Extension("httptools.parser.parser",
                  ["httptools/parser/parser.c",
                   "vendor/http-parser/http_parser.c"],
                  extra_compile_args=['-O2'])
    ],
    provides=['httptools'],
    include_package_data=True
)
