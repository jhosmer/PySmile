#!/usr/bin/env python
import os
import glob
import unittest
import pysmile

__author__ = 'Jonathan Hosmer'


class PySmileTest(unittest.TestCase):
    def setUp(self):
        curdir = os.path.dirname(os.path.abspath(__file__))
        self.smile_dir = os.path.join(curdir, 'data', 'smile')
        self.json_dir = os.path.join(curdir, 'data', 'json')

    def test_test1(self):
        s = os.path.join(self.smile_dir, 'test1.smile')
        j = os.path.join(self.json_dir, os.path.splitext(os.path.basename(s))[0] + '.jsn')
        self.assertEqual(pysmile.decode(open(s, 'rb').read()), open(j, 'rb').read(), s)

    def test_test2(self):
        s = os.path.join(self.smile_dir, 'test2.smile')
        j = os.path.join(self.json_dir, os.path.splitext(os.path.basename(s))[0] + '.jsn')
        self.assertEqual(pysmile.decode(open(s, 'rb').read()), open(j, 'rb').read(), s)

    def test_json_org_sample1(self):
        s = os.path.join(self.smile_dir, 'json-org-sample1.smile')
        j = os.path.join(self.json_dir, os.path.splitext(os.path.basename(s))[0] + '.jsn')
        self.assertEqual(pysmile.decode(open(s, 'rb').read()), open(j, 'rb').read(), s)

    def test_json_org_sample2(self):
        s = os.path.join(self.smile_dir, 'json-org-sample2.smile')
        j = os.path.join(self.json_dir, os.path.splitext(os.path.basename(s))[0] + '.jsn')
        self.assertEqual(pysmile.decode(open(s, 'rb').read()), open(j, 'rb').read(), s)

    def test_json_org_sample3(self):
        s = os.path.join(self.smile_dir, 'json-org-sample3.smile')
        j = os.path.join(self.json_dir, os.path.splitext(os.path.basename(s))[0] + '.jsn')
        self.assertEqual(pysmile.decode(open(s, 'rb').read()), open(j, 'rb').read(), s)

    def test_json_org_sample4(self):
        s = os.path.join(self.smile_dir, 'json-org-sample4.smile')
        j = os.path.join(self.json_dir, os.path.splitext(os.path.basename(s))[0] + '.jsn')
        self.assertEqual(pysmile.decode(open(s, 'rb').read()), open(j, 'rb').read(), s)

    def test_json_org_sample5(self):
        s = os.path.join(self.smile_dir, 'json-org-sample5.smile')
        j = os.path.join(self.json_dir, os.path.splitext(os.path.basename(s))[0] + '.jsn')
        self.assertEqual(pysmile.decode(open(s, 'rb').read()), open(j, 'rb').read(), s)

    def test_numbers_int_4k(self):
        s = os.path.join(self.smile_dir, 'numbers-int-4k.smile')
        j = os.path.join(self.json_dir, os.path.splitext(os.path.basename(s))[0] + '.jsn')
        self.assertEqual(pysmile.decode(open(s, 'rb').read()), open(j, 'rb').read(), s)

    def test_numbers_int_64k(self):
        s = os.path.join(self.smile_dir, 'numbers-int-64k.smile')
        j = os.path.join(self.json_dir, os.path.splitext(os.path.basename(s))[0] + '.jsn')
        self.assertEqual(pysmile.decode(open(s, 'rb').read()), open(j, 'rb').read(), s)
