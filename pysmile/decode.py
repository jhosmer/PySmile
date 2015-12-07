"""
SMILE Decode
"""
import os
import json
import struct
import logging

from pysmile.constants import *
from pysmile import util

log = logging.getLogger()
if not log.handlers:
    log.addHandler(logging.NullHandler())

__author__ = 'Jonathan Hosmer'


class DecodeError(StandardError):
    pass


class DecodeMode(object):
    HEAD = 0       # Waiting for magic header :)
    ROOT = 1       # Waiting for Root object
    ARRAY = 2      # In array context
    VALUE = 3      # Waiting for value
    KEY = 4        # Waiting for key
    DONE = 5       # Done -- remain here until reset
    BAD = 6        # Got a data error -- remain here until reset


class SmileHeader(object):
    def __init__(self, version, raw_bin=True, shared_names=True, shared_values=False):
        self.version = version
        self.raw_binary = raw_bin
        self.shared_keys = shared_names
        self.shared_values = shared_values


class DecodeState(object):
    def __init__(self, string):
        if isinstance(string, unicode):
            string = string.encode('UTF-8')
        self.s = bytearray(string)
        """Input"""

        self.out = []
        """Output"""

        self.mode = DecodeMode.HEAD
        """Current Decoder State"""

        self.error = None
        """Error message"""

        self.index = 0
        """Current read index"""

        self.nested_depth = 0
        """current nest level"""

        self.in_array = [False] * 30
        """true if in array context"""

        self.first_array_element = [False] * 30
        """# true if the next token is the first value of an array (used for printing)"""

        self.first_key = [False] * 30
        """true if the next token is the first key of an object (used for printing)"""

        self.header = None
        """smile header"""

        self.shared_key_strings = []
        """Cached Keys for back references"""

        self.shared_value_strings = []
        """Cached Values for back references"""

    def pull_byte(self):
        ret_s = None
        try:
            ret_s = self.s[self.index]
        except IndexError:
            self.mode = DecodeMode.DONE
        else:
            self.index += 1
        return ret_s

    def pull_bits(self, n):
        ret_s = bytearray()
        for _ in xrange(abs(n)):
            b = self.pull_byte()
            if b is None:
                break
            ret_s.append(b)
        return ret_s

    def write(self, *args):
        if args:
            self.out.extend(args)

    def get_value(self):
        return ''.join(map(str, self.out))

    @staticmethod
    def _escape(o):
        return str(o).replace('\n', r'\n').replace('"', r'\"')

    def save_key_string(self, key_str):
        log.debug('key_str: {!r}'.format(key_str))
        self.shared_key_strings.append(key_str)

    def save_value_string(self, val_str):
        log.debug('val_str: {!r}'.format(val_str))
        self.shared_value_strings.append(val_str)

    def copy_key_string(self, n=0):
        key_str = self._escape(self.s[self.index:self.index + n])
        if self.header.shared_keys:
            self.save_key_string(key_str)
        self.write('"', key_str, '":')
        self.index += n

    def copy_value_string(self, n=0):
        val_str = self._escape(self.s[self.index:self.index + n])
        if self.header.shared_values:
            self.save_value_string(val_str)
        self.write('"', val_str, '"')
        self.index += n

    def copy_shared_key_string(self):
        if not self.header.shared_keys:
            raise DecodeError('Cannot lookup shared key, sharing disabled!')
        try:
            sh_str = self.shared_key_strings[self.s[self.index - 1] - 0x40]
        except IndexError:
            sh_str = ''
            # print repr(self.shared_key_strings)
            # print repr(self.s[self.index - 1:self.index+1])
        else:
            self.write('"', sh_str, '":')

    def copy_shared_value_string(self):
        if not self.header.shared_values:
            raise DecodeError('Cannot lookup shared value, sharing disabled!')
        self.write('"', self.shared_value_strings[self.s[self.index - 1] - 1], '"')

    def copy_variable_length_string(self):
        i = self.s.index('\xfc', self.index)
        self.write('"', self._escape(self.s[self.index:i]), '"')
        self.index = i+1

    def varint_decode(self):
        smile_zzvarint_decode = 0
        tmp = self.s[self.index:]
        for i, ch in enumerate(tmp):
            self.index += 1
            if ch & 0x80:
                smile_zzvarint_decode <<= 6
                smile_zzvarint_decode |= (ch & 0x3F)
                break
            smile_zzvarint_decode <<= 7
            smile_zzvarint_decode |= ch
        return smile_zzvarint_decode

    def zzvarint_decode(self):
        self.write(util.zigzag_decode(self.varint_decode()))


def decode(fp):
    """
    Decode SMILE file

    :param FileIO fp: File-like object with SMILE encoded data
    :returns: Decoded python object
    :rtype: list|dict

    >>> import pysmile
    >>> pysmile.decode(open('smile.smile', 'rb'))
    """
    if isinstance(fp, basestring):
        if os.path.isfile(fp):
            fp_str = open(fp, 'rb').read()
        else:
            fp_str = fp
    elif hasattr(fp, 'read'):
        fp_str = fp.read()
    return decodes(fp_str)


def decodes(string):
    """
    Decode SMILE string

    :param str string: SMILE formatted data string
    :returns: Decoded python object
    :rtype: list|dict

    >>> import pysmile
    >>> assert pysmile.decodes(''':)\n\x03\xf8\xc2\xf9''') == [1]
    >>> assert pysmile.decodes(''':)\n\x03\xf8\xc2\xc4\xf9''') == [1, 2]
    >>> assert pysmile.decodes(''':)\n\x03\xf8\xc2\xc4\xfa\x80c\xc6\xfb\xf9''') == [1, 2, {"c": 3}]
    """
    log.debug('Decoding: {!r}'.format(string))
    state = DecodeState(string)
    while state.mode not in (DecodeMode.BAD, DecodeMode.DONE):
        if state.mode == DecodeMode.HEAD:
            head = state.pull_bits(3)
            if not (head and head.startswith(HEADER_BYTE_1+HEADER_BYTE_2+HEADER_BYTE_3)):
                state.mode = DecodeMode.BAD
                state.error = 'Invalid Header!'
                continue
            state.mode = DecodeMode.ROOT
            features = state.pull_byte()
            version = features & HEADER_BIT_VERSION
            shared_keys = bool(features & HEADER_BIT_HAS_SHARED_NAMES)
            shared_values = bool((features & HEADER_BIT_HAS_SHARED_STRING_VALUES) >> 1)
            raw_binary = bool((features & HEADER_BIT_HAS_RAW_BINARY) >> 2)
            state.header = SmileHeader(version, raw_binary, shared_keys, shared_values)
        elif state.mode in (DecodeMode.ROOT, DecodeMode.ARRAY, DecodeMode.VALUE):
            b = state.pull_byte()
            if b is None:
                log.debug('No bytes left to read!')
                continue
            log.debug('Pulled Byte: 0x{:x}'.format(b))

            if state.in_array[state.nested_depth]:
                if state.first_array_element[state.nested_depth]:
                    state.first_array_element[state.nested_depth] = False
                elif b != TOKEN_LITERAL_END_ARRAY:
                    state.write(',')
            if b == NULL_BIT:
                log.debug('Token: Null Bit (skip)')
            elif HEADER_BIT_HAS_SHARED_NAMES <= b <= 0x1f:
                log.debug('Token: Shared Value String')
                state.copy_shared_value_string()
            elif TOKEN_LITERAL_EMPTY_STRING <= b <= TOKEN_LITERAL_TRUE:
                # Simple literals, numbers
                if b == TOKEN_LITERAL_EMPTY_STRING:
                    log.debug('Token: Empty String')
                    state.write('""')
                elif b == TOKEN_LITERAL_NULL:
                    log.debug('Token: Literal Null')
                    state.write('null')
                elif b == TOKEN_LITERAL_FALSE:
                    log.debug('Token: Literal False')
                    state.write('false')
                elif b == TOKEN_LITERAL_TRUE:
                    log.debug('Token: Literal True')
                    state.write('true')
            elif TOKEN_PREFIX_INTEGER <= b < TOKEN_PREFIX_FP:
                # Integral numbers
                log.debug('Token: Integral Numbers')
                smile_value_length = b & 0x03
                if smile_value_length < 2:
                    state.zzvarint_decode()
                elif smile_value_length == 2:
                    # BigInteger
                    log.warn('Not Yet Implemented: Value BigInteger')
                else:
                    # Reserved for future use
                    log.warn('Reserved: integral numbers with length >= 3')
            elif TOKEN_PREFIX_FP <= b <= 0x2B:
                # Floating point numbers
                if b == TOKEN_BYTE_FLOAT_32:
                    fp = state.pull_bits(5)
                    b1 = fp[0]
                    b2 = fp[1] << 7
                    b3 = fp[2] << 7 << 7
                    b4 = fp[3] << 7 << 7 << 7
                    b5 = fp[4] << 7 << 7 << 7 << 7
                    b = (b1 | b2 | b3 | b4 | b5)
                    try:
                        flt = util.bits_to_float(b)
                    except struct.error:
                        flt = util.long_bits_to_float(b)
                    state.write(flt)
                elif b == TOKEN_BYTE_FLOAT_64:
                    fp = state.pull_bits(9)
                    b1 = fp[0]
                    b2 = fp[1] << 7
                    b3 = fp[2] << 7 << 7
                    b4 = fp[3] << 7 << 7 << 7
                    b5 = fp[4] << 7 << 7 << 7 << 7
                    b6 = fp[4] << 7 << 7 << 7 << 7 << 7
                    b7 = fp[4] << 7 << 7 << 7 << 7 << 7 << 7
                    b8 = fp[4] << 7 << 7 << 7 << 7 << 7 << 7 << 7
                    b9 = fp[4] << 7 << 7 << 7 << 7 << 7 << 7 << 7 << 7
                    b = (b1 | b2 | b3 | b4 | b5 | b6 | b7 | b8 | b9)
                    flt = util.long_bits_to_float(b)
                    state.write(flt)
                else:
                    log.warn('Not Yet Implemented')
            elif 0x2C <= b <= 0x3F:
                # Reserved for future use
                log.warn('Reserved: 0x2C <= value <= 0x3F')
            elif 0x40 <= b <= 0x5F or 0x80 <= b <= 0x9F:
                # Tiny ASCII/Unicode
                log.debug('Token: Tiny ASCII/Unicode')
                smile_value_length = (b & 0x1F) + 1
                state.copy_value_string(smile_value_length)
            elif 0x60 <= b <= 0x7F or 0xA0 <= b <= 0xBF:
                # Small ASCII/Unicode
                log.debug('Token: Small ASCII/Unicode')
                smile_value_length = (b & 0x1F) + 33
                state.copy_value_string(smile_value_length)
            elif 0xC0 <= b <= 0xDF:
                # Small Integers
                log.debug('Token: Small Integer')
                state.write(util.zigzag_decode(b & 0x1F))
            else:
                # Misc binary / text / structure markers
                if TOKEN_MISC_LONG_TEXT_ASCII <= b < TOKEN_MISC_LONG_TEXT_UNICODE:
                    # Long (variable length) ASCII text
                    log.debug('Token: Long (var length) ASCII Test')
                    state.copy_variable_length_string()
                elif TOKEN_MISC_LONG_TEXT_UNICODE <= b < INT_MISC_BINARY_7BIT:
                    log.warn('Not Yet Implemented: Value Long Unicode')
                elif INT_MISC_BINARY_7BIT <= b < TOKEN_PREFIX_SHARED_STRING_LONG:
                    log.warn('Not Yet Implemented: Value Long Shared String Reference')
                elif TOKEN_PREFIX_SHARED_STRING_LONG <= b < HEADER_BIT_VERSION:
                    # Binary, 7-bit encoded
                    log.warn('Not Yet Implemented: Value Binary')
                elif HEADER_BIT_VERSION <= b < TOKEN_LITERAL_START_ARRAY:
                    log.warn('Reserved: 0xF0 <= value <= 0xF8')
                elif b == TOKEN_LITERAL_START_ARRAY:
                    # START_ARRAY
                    log.debug('Token: Start Array')
                    state.write('[')
                    state.nested_depth += 1
                    state.in_array[state.nested_depth] = True
                    state.first_array_element[state.nested_depth] = True
                    state.first_key[state.nested_depth] = False
                elif b == TOKEN_LITERAL_END_ARRAY:
                    # END_ARRAY
                    log.debug('Token: End Array')
                    state.write(']')
                    state.nested_depth -= 1
                elif b == TOKEN_LITERAL_START_OBJECT:
                    # START_OBJECT
                    log.debug('Token: Start Object')
                    state.write('{')
                    state.nested_depth += 1
                    state.in_array[state.nested_depth] = False
                    state.first_array_element[state.nested_depth] = False
                    state.first_key[state.nested_depth] = True
                    state.mode = DecodeMode.KEY
                    continue
                elif b == TOKEN_LITERAL_END_OBJECT:
                    log.debug('Token: End Object')
                    log.warn('Reserved: value == 0xFB')
                elif b == BYTE_MARKER_END_OF_STRING:
                    log.error('Found end-of-String marker 0xFC in value mode')
                elif b == INT_MISC_BINARY_RAW:
                    log.warn('Not Yet Implemented: Raw Binary Data')
                elif b == BYTE_MARKER_END_OF_CONTENT:
                    # Optional end marker
                    log.debug('Token: End Marker')
                    state.mode = DecodeMode.DONE
                    continue
            if not state.in_array[state.nested_depth]:
                state.mode = DecodeMode.KEY
        elif state.mode == DecodeMode.KEY:
            b = state.pull_byte()
            if b is None:
                log.debug('No bytes left to read!')
                continue
            log.debug('Pulled Byte: 0x{:x}'.format(b))

            if state.first_key[state.nested_depth]:
                state.first_key[state.nested_depth] = False
            elif b != TOKEN_LITERAL_END_OBJECT:
                state.write(',')

            # Byte ranges are divided in 4 main sections (64 byte values each)
            if 0x00 <= b <= 0x1F:
                # Reserved for future use
                log.warn('Reserved: 0x01 <= key <= 0x1F')
            elif b == TOKEN_LITERAL_EMPTY_STRING:
                # Empty String
                log.debug('Token: Literal Empty String')
                state.write('""')
            elif TOKEN_LITERAL_NULL <= b <= 0x2F:
                # Reserved for future use
                log.warn('Reserved: 0x21 <= key <= 0x2F')
            elif TOKEN_PREFIX_KEY_SHARED_LONG <= b <= 0x33:
                # "Long" shared key name reference
                log.warn('Not Yet Implemented: Long Shared Key Name Reference')
            elif b == 0x32:
                # Long (not-yet-shared) Unicode name, 64 bytes or more
                log.warn('Not Yet Implemented: Long Key Name')
            elif 0x35 <= b <= 0x39:
                # Reserved for future use
                log.warn('Reserved: 0x35 <= key <= 0x39')
            elif b == 0x3A:
                # Error
                log.error('0x3A NOT allowed in Key mode')
            elif 0x3B <= b <= 0x3F:
                # Reserved for future use
                log.warn('Reserved: 0x3B <= key <= 0x3F')
            elif TOKEN_PREFIX_KEY_SHARED_SHORT <= b <= 0x7F:
                # "Short" shared key name reference (1 byte lookup)
                log.debug('Token: Short Shared Key Name Reference')
                state.copy_shared_key_string()
            elif TOKEN_PREFIX_KEY_ASCII <= b <= 0xBF:
                # Short Ascii names
                # 5 LSB used to indicate lengths from 2 to 32 (bytes == chars)
                log.debug('Token: Short ASCII Name')
                smile_key_length = (b & 0x1F) + 1
                state.copy_key_string(smile_key_length)
            elif TOKEN_PREFIX_KEY_UNICODE <= b <= TOKEN_RESERVED:
                # Short Unicode names
                # 5 LSB used to indicate lengths from 2 to 57
                log.debug('Token: Short Unicode Name')
                smile_key_length = (b - 0xC0) + 2
                state.copy_key_string(smile_key_length)
            elif TOKEN_LITERAL_START_ARRAY <= b <= TOKEN_LITERAL_START_OBJECT:
                # Reserved
                log.warn('Reserved: 0xF8 <= key <= 0xFA')
            elif b == TOKEN_LITERAL_END_OBJECT:
                # END_OBJECT marker
                log.debug('Token: Literal End Object')
                state.write('}')
                state.nested_depth -= 1
                try:
                    in_arry = state.in_array[state.nested_depth]
                except IndexError:
                    in_arry = False
                if in_arry:
                    state.mode = DecodeMode.VALUE
                else:
                    state.mode = DecodeMode.KEY
                continue
            elif b >= BYTE_MARKER_END_OF_STRING:
                # Reserved
                log.warn('Reserved: key >= 0xFC')
            state.mode = DecodeMode.VALUE
        elif state.mode == DecodeMode.BAD:
            if state.error is None:
                state.error = 'Unknown Error!'
            break
        elif state.mode == DecodeMode.DONE:
            log.debug('Decoding Done!')
            break
    if state.mode == DecodeMode.BAD:
        raise DecodeError('Bad State: {}'.format(state.error), state.get_value())
    ret_val = state.get_value()
    try:
        jsonified = json.loads(ret_val)
    except (ValueError, UnicodeDecodeError):
        msg = 'Unable to jsonify string: {!r}'.format(ret_val)
        log.exception(msg)
        raise DecodeError(msg)
    return jsonified
    # return state.get_value()

if __name__ == '__main__':
    a = {'a': '1', 'b': 2, 'c': [3], 'd': -1, 'e': 4.20}
    b = decodes(':)\n\x03\xfa\x80a@1\x80c\xf8\xc6\xf9\x80b\xc4\x80e(fL\x19\x04\x04\x80d\xc1\xfb')
    if a != b:
        print repr(a)
        print repr(b)

    a = {'a': {'b': {'c': {'d': ['e']}}}}
    b = decode(':)\n\x03\xfa\x80a\xfa\x80b\xfa\x80c\xfa\x80d\xf8@e\xf9\xfb\xfb\xfb\xfb')
    if a != b:
        print repr(a)
        print repr(b)
