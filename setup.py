#!/usr/bin/env python
from setuptools import setup, Extension

c_sources = [
    'pysmile/_pysmile.c',
    'pysmile/libsmile/lib/block.c',
    'pysmile/libsmile/lib/decode.c'
]
extra_compile_args = [
    '-std=c99',
    '-pedantic',
    '-Wall',
    '-O2',
    '-fomit-frame-pointer',
    '-Wno-tautological-compare',
    '-Ipysmile/libsmile/include'
]

setup(name='pysmile',
      author='Jonathan Hosmer',
      author_email='jon@pythonforios.com',
      description='Tools for working with the SMILE data format',
      license='Apache License, Version 2.0',
      keywords='json smile',
      url='https://github.com/jhosmer/PySmile',
      packages=['pysmile'],
      platforms=['Linux'],
      long_description='README',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Topic :: Utilities',
      ],
      test_suite='test.pysmile_test',
      version='0.1',
      # ext_modules=[Extension('_pysmile', c_sources, extra_compile_args=extra_compile_args)]
)
