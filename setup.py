#!/usr/bin/env python
import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(os.path.abspath(__file__)), fname)).read()


setup(
    name='pysmile',
    author='Jonathan Hosmer',
    author_email='jon@pythonforios.com',
    description='Tools for working with the SMILE data format',
    license='Apache License, Version 2.0',
    keywords='json smile',
    url='https://github.com/jhosmer/PySmile',
    packages=['pysmile', 'tests'],
    platforms=['Linux'],
    long_description=read('README'),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: Unix',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
        'Topic :: Utilities',
    ],
    test_suite='tests.pysmile_tests',
    version='0.1'
)
