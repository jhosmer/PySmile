#!/usr/bin/env python
from setuptools import setup, Extension

ext = Extension('pysmile',
                ['src/pysmile.c', 'src/libsmile/block.c', 'src/libsmile/decode.c'],
                extra_compile_args=['-std=c99', '-pedantic', '-Wall', '-O2',
                                    '-fomit-frame-pointer', '-Wno-tautological-compare',
                                    '-Isrc/libsmile/', '-Isrc/libsmile/include'])

setup(name='pysmile',
      author='Jonathan Hosmer',
      author_email='jon@pythonforios.com',
      description='Tools for working with the SMILE data format',
      license='Other/Propriatary',
      keywords='json smile',
      url='http://coming.soon/pysmile',  # TODO: FIXME
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
      ext_modules=[ext])
