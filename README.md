# PySmile

`python setup.py clean build test`


### Example Usage:

    In [1]: import pysmile
    In [2]: d = open('test/data/smile/test1.smile', 'rb').read()
    In [3]: d
    Out[3]: ':)\n\x03\xfa\x87test key#\x88nullField!\x82foo\xc2\x83foo2\xfa\x80a\xc6\xfb\xc2a\xc3\xa3b$\n\x85\x802\xf8\xc2\xc4\xc6\xf9\x84"foo"Ffoo\nbar\xfb'
    In [4]: pysmile.decode(d)
    Out[4]: '{"test key":true,"nullField":null,"foo":1,"foo2":{"a":3},"a\xc3\xa3b":-323,"2":[1,2,3],"\\"foo\\"":"foo\\nbar"}'
    In [5]: import json
    In [6]: json.loads(pysmile.decode(d))
    Out[6]: 
    {u'"foo"': u'foo\nbar',
     u'2': [1, 2, 3],
     u'a\xe3b': -323,
     u'foo': 1,
     u'foo2': {u'a': 3},
     u'nullField': None,
     u'test key': True}
    In [7]: json.load(open('test/data/json/test1.jsn'))
    Out[7]: 
    {u'"foo"': u'foo\nbar',
     u'2': [1, 2, 3],
     u'a\xe3b': -323,
     u'foo': 1,
     u'foo2': {u'a': 3},
     u'nullField': None,
     u'test key': True}
    In [8]: assert pysmile.decode(d) == open('test/data/json/test1.jsn').read()
