#!/usr/bin/env python
from setuptools import setup

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
      version='0.1'
)
