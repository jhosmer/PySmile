#!/usr/bin/env python
import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='pysmile',
    author='Jonathan Hosmer',
    author_email='jon@pythonforios.com',
    description='Tools for working with the SMILE data format',
    license='Apache License, Version 2.0',
    keywords='json smile',
    url='https://github.com/jhosmer/PySmile',
    packages=['pysmile', 'test'],
    platforms=['Linux'],
    long_description=read('README'),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Topic :: Utilities',
    ],
    test_suite='test.pysmile_test',
    version='0.1'
)
