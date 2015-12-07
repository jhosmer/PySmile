#!/usr/bin/env python
import os
import glob
import unittest
import pysmile
import json

__author__ = 'Jonathan Hosmer'


class PySmileTestDecode(unittest.TestCase):
    def setUp(self):
        curdir = os.path.dirname(os.path.abspath(__file__))
        self.smile_dir = os.path.join(curdir, 'data', 'smile')
        self.json_dir = os.path.join(curdir, 'data', 'json')

    def test_test(self):
        for x in xrange(1, 3):
            s = os.path.join(self.smile_dir, 'test{}.smile'.format(x))
            j = os.path.join(self.json_dir, 'test{}.jsn'.format(x))
            a = pysmile.decode(open(s, 'rb').read())
            b = json.load(open(j, 'rb'))
            if isinstance(a, list):
                self.assertListEqual(a, b, '{}\nExpected:\n{!r}\nGot:\n{!r}'.format(s, a, b))
            elif isinstance(a, dict):
                self.assertDictEqual(a, b, '{}\nExpected:\n{!r}\nGot:\n{!r}'.format(s, a, b))
            else:
                self.fail('Unexpected Type: {!r}'.format(type(a)))

    def test_json_org_sample(self):
        for x in xrange(1, 6):
            s = os.path.join(self.smile_dir, 'json-org-sample{}.smile'.format(x))
            j = os.path.join(self.json_dir, 'json-org-sample{}.jsn'.format(x))
            a = pysmile.decode(open(s, 'rb').read())
            b = json.load(open(j, 'rb'))
            if isinstance(a, list):
                self.assertListEqual(a, b, '{}\nExpected:\n{!r}\nGot:\n{!r}'.format(s, a, b))
            elif isinstance(a, dict):
                self.assertDictEqual(a, b, '{}\nExpected:\n{!r}\nGot:\n{!r}'.format(s, a, b))
            else:
                self.fail('Unexpected Type: {!r}'.format(type(a)))

    def test_numbers_int_4k(self):
        s = os.path.join(self.smile_dir, 'numbers-int-4k.smile')
        j = os.path.join(self.json_dir, 'numbers-int-4k.jsn')
        a = pysmile.decode(open(s, 'rb').read())
        b = json.load(open(j, 'rb'))
        if isinstance(a, list):
            self.assertListEqual(a, b, '{}\nExpected:\n{!r}\nGot:\n{!r}'.format(s, a, b))
        elif isinstance(a, dict):
            self.assertDictEqual(a, b, '{}\nExpected:\n{!r}\nGot:\n{!r}'.format(s, a, b))
        else:
            self.fail('Unexpected Type: {!r}'.format(type(a)))

    def test_numbers_int_64k(self):
        s = os.path.join(self.smile_dir, 'numbers-int-64k.smile')
        j = os.path.join(self.json_dir, 'numbers-int-64k.jsn')
        a = pysmile.decode(open(s, 'rb').read())
        b = json.load(open(j, 'rb'))
        if isinstance(a, list):
            self.assertListEqual(a, b, '{}\nExpected:\n{!r}\nGot:\n{!r}'.format(s, a, b))
        elif isinstance(a, dict):
            self.assertDictEqual(a, b, '{}\nExpected:\n{!r}\nGot:\n{!r}'.format(s, a, b))
        else:
            self.fail('Unexpected Type: {!r}'.format(type(a)))


class PySmileTestEncode(unittest.TestCase):
    def setUp(self):
        curdir = os.path.dirname(os.path.abspath(__file__))
        self.smile_dir = os.path.join(curdir, 'data', 'smile')
        self.json_dir = os.path.join(curdir, 'data', 'json')

    def test_test(self):
        for x in xrange(2, 3):
            s = os.path.join(self.smile_dir, 'test{}.smile'.format(x))
            j = os.path.join(self.json_dir, 'test{}.jsn'.format(x))
            a = pysmile.encode(json.load(open(j, 'rb')))
            b = open(s, 'rb').read()
            self.assertEqual(a, b, '{}\nExpected:\n{!r}\nGot:\n{!r}'.format(s, a, b))

    def test_json_org_sample(self):
        for x in xrange(5, 6):
            s = os.path.join(self.smile_dir, 'json-org-sample{}.smile'.format(x))
            j = os.path.join(self.json_dir, 'json-org-sample{}.jsn'.format(x))
            a = pysmile.encode(json.load(open(j, 'rb')))
            b = open(s, 'rb').read()
            self.assertEqual(a, b, '{}\nExpected:\n{!r}\nGot:\n{!r}'.format(s, a, b))

    def test_numbers_int_4k(self):
        s = os.path.join(self.smile_dir, 'numbers-int-4k.smile')
        j = os.path.join(self.json_dir, 'numbers-int-4k.jsn')
        a = pysmile.encode(json.load(open(j, 'rb')))
        b = open(s, 'rb').read()
        self.assertEqual(a, b, '{}\nExpected:\n{!r}\nGot:\n{!r}'.format(s, a, b))

    def test_numbers_int_64k(self):
        s = os.path.join(self.smile_dir, 'numbers-int-64k.smile')
        j = os.path.join(self.json_dir, 'numbers-int-64k.jsn')
        a = pysmile.encode(json.load(open(j, 'rb')))
        b = open(s, 'rb').read()
        self.assertEqual(a, b, '{}\nExpected:\n{!r}\nGot:\n{!r}'.format(s, a, b))


class PySmileTestMisc(unittest.TestCase):
    def test_1(self):
        a = [1]
        b = pysmile.decode(':)\n\x03\xf8\xc2\xf9')
        self.assertListEqual(a, b, 'Expected:\n{!r}\nGot:\n{!r}'.format(a, b))

    def test_2(self):
        a = [1, 2]
        b = pysmile.decode(':)\n\x03\xf8\xc2\xc4\xf9')
        self.assertListEqual(a, b, 'Expected:\n{!r}\nGot:\n{!r}'.format(a, b))

    def test_3(self):
        a = [1, 2, {'c': 3}]
        b = pysmile.decode(':)\n\x03\xf8\xc2\xc4\xfa\x80c\xc6\xfb\xf9')
        self.assertListEqual(a, b, 'Expected:\n{!r}\nGot:\n{!r}'.format(a, b))

    def test_4(self):
        a = {'a': 1}
        b = pysmile.decode(':)\n\x03\xfa\x80a\xc2\xfb')
        self.assertDictEqual(a, b, 'Expected:\n{!r}\nGot:\n{!r}'.format(a, b))

    def test_5(self):
        a = {'a': '1', 'b': 2, 'c': [3], 'd': -1, 'e': 4.20}
        b = pysmile.decode(
            ':)\n\x03\xfa\x80a@1\x80c\xf8\xc6\xf9\x80b\xc4\x80e(fL\x19\x04\x04\x80d\xc1\xfb')
        self.assertDictEqual(a, b, 'Expected:\n{!r}\nGot:\n{!r}'.format(a, b))

    def test_6(self):
        a = {'a': {'b': {'c': {'d': ['e']}}}}
        b = pysmile.decode(
                ':)\n\x03\xfa\x80a\xfa\x80b\xfa\x80c\xfa\x80d\xf8@e\xf9\xfb\xfb\xfb\xfb')
        self.assertDictEqual(a, b, 'Expected:\n{!r}\nGot:\n{!r}'.format(a, b))
