
def generate_tests():
    import re
    import os

    curdir = os.path.dirname(os.path.abspath(__file__))
    smile_dir = os.path.join(curdir, 'data', 'smile')
    json_dir = os.path.join(curdir, 'data', 'json')

    file_header = '''\
#!/usr/bin/env python
import os
import glob
import unittest
import pysmile
import json

__author__ = 'Jonathan Hosmer'
    '''

    setup = '''
    def setUp(self):
        curdir = os.path.dirname(os.path.abspath(__file__))
        self.smile_dir = os.path.join(curdir, 'data', 'smile')
        self.json_dir = os.path.join(curdir, 'data', 'json')
'''

    decode_tests = '''

class PySmileTestDecode(unittest.TestCase):''' + setup

    encode_tests = '''

class PySmileTestEncode(unittest.TestCase):''' + setup

    file_footer = '''

class PySmileTestMisc(unittest.TestCase):
    def test_1(self):
        a = [1]
        b = pysmile.decode(':)\\n\\x03\\xf8\\xc2\\xf9')
        self.assertListEqual(a, b, 'Expected:\\n{!r}\\nGot:\\n{!r}'.format(a, b))

    def test_2(self):
        a = [1, 2]
        b = pysmile.decode(':)\\n\\x03\\xf8\\xc2\\xc4\\xf9')
        self.assertListEqual(a, b, 'Expected:\\n{!r}\\nGot:\\n{!r}'.format(a, b))

    def test_3(self):
        a = [1, 2, {'c': 3}]
        b = pysmile.decode(':)\\n\\x03\\xf8\\xc2\\xc4\\xfa\\x80c\\xc6\\xfb\\xf9')
        self.assertListEqual(a, b, 'Expected:\\n{!r}\\nGot:\\n{!r}'.format(a, b))

    def test_4(self):
        a = {'a': 1}
        b = pysmile.decode(':)\\n\\x03\\xfa\\x80a\\xc2\\xfb')
        self.assertDictEqual(a, b, 'Expected:\\n{!r}\\nGot:\\n{!r}'.format(a, b))

    def test_5(self):
        a = {'a': '1', 'b': 2, 'c': [3], 'd': -1, 'e': 4.20}
        b = pysmile.decode(
            ':)\\n\\x03\\xfa\\x80a@1\\x80c\\xf8\\xc6\\xf9\\x80b\\xc4\\x80e(fL\\x19\\x04\\x04\\x80d\\xc1\\xfb')
        self.assertDictEqual(a, b, 'Expected:\\n{!r}\\nGot:\\n{!r}'.format(a, b))

    def test_6(self):
        a = {'a': {'b': {'c': {'d': ['e']}}}}
        b = pysmile.decode(
                ':)\\n\\x03\\xfa\\x80a\\xfa\\x80b\\xfa\\x80c\\xfa\\x80d\\xf8@e\\xf9\\xfb\\xfb\\xfb\\xfb')
        self.assertDictEqual(a, b, 'Expected:\\n{!r}\\nGot:\\n{!r}'.format(a, b))
'''

    for smile in os.listdir(smile_dir):
        base_name = os.path.basename(os.path.join(json_dir, re.sub('\.smile$', '', smile, 1)))
        json = base_name + '.jsn'

        tname = re.sub('[-.]', '_', base_name)
        decode_tests += '''
    def test_{tname}(self):
        s = os.path.join(self.smile_dir, '{smile}')
        j = os.path.join(self.json_dir, '{json}')
        b = json.load(open(j, 'rb'))
        try:
            a = pysmile.decode(open(s, 'rb').read())
        except pysmile.SMILEDecodeError, e:
            self.fail('Failed to decode:\\n{{!r}}\\n{{!r}}'.format(b, e.args[1]))
        else:
            if isinstance(a, list):
                self.assertListEqual(a, b, '{{}}\\nExpected:\\n{{!r}}\\nGot:\\n{{!r}}'.format(s, b, a))
            elif isinstance(a, dict):
                self.assertDictEqual(a, b, '{{}}\\nExpected:\\n{{!r}}\\nGot:\\n{{!r}}'.format(s, b, a))
            else:
                self.fail('Unexpected Type: {{!r}}'.format(type(a)))
    '''.format(tname=tname, smile=smile, json=json)

        encode_tests += '''
    def test_{tname}(self):
        s = os.path.join(self.smile_dir, '{smile}')
        j = os.path.join(self.json_dir, '{json}')
        a = pysmile.encode(json.load(open(j, 'rb')))
        b = open(s, 'rb').read()
        self.assertEqual(a, b, '{{}}\\nExpected:\\n{{!r}}\\nGot:\\n{{!r}}'.format(s, b, a))
    '''.format(tname=tname, smile=smile, json=json)

    with open(os.path.join(curdir, 'pysmile_tests.py'), 'w') as outfile:
        outfile.write(file_header + decode_tests + encode_tests + file_footer + '\n')

if __name__ == '__main__':
    generate_tests()
