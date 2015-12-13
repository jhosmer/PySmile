#!/usr/bin/env python
"""
SMILE Encode
"""
import re
import sys
import struct
import decimal
import copy
import logging
import json
import json.encoder

from pysmile.constants import *
from pysmile import util

log = logging.getLogger()
if not log.handlers:
    log.addHandler(logging.NullHandler())

__author__ = 'Jonathan Hosmer'


def _utf_8_encode(s):
    try:
        return s.encode('UTF-8')
    except UnicodeEncodeError:
        return s


class SMILEEncodeError(StandardError):
    pass


class SharedStringNode(object):
    """
    Helper class used for keeping track of possibly shareable String references (for field names
    and/or short String values)
    """
    def __init__(self, value, index, nxt):
        self.value = value
        self.index = index
        self.next = nxt


class SmileGenerator(object):
    """
    To simplify certain operations, we require output buffer length
    to allow outputting of contiguous 256 character UTF-8 encoded String
    value. Length of the longest UTF-8 code point (from Java char) is 3 bytes,
    and we need both initial token byte and single-byte end marker
    so we get following value.

    Note: actually we could live with shorter one; absolute minimum would be for encoding
    64-character Strings.
    """

    def __init__(self, shared_keys=True, shared_values=True, encode_as_7bit=True):
        """
        SmileGenerator Initializer

        :param bool encode_as_7bit: (optional - Default: `True`) Encode raw data as 7-bit
        :param bool shared_keys: (optional - Default: `True`) Shared Key String References
        :param bool shared_values: (optional - Default: `True`) Shared Value String References
        """
        # Encoded data
        self.output = bytearray()

        # Shared Key Strings
        self.shared_keys = []

        # Shared Value Strings
        self.shared_values = []

        self.share_keys = bool(shared_keys)
        self.share_values = bool(shared_values)
        self.encode_as_7bit = bool(encode_as_7bit)

    def write_header(self):
        """
        Method that can be called to explicitly write Smile document header.
        Note that usually you do not need to call this for first document to output,
        but rather only if you intend to write multiple root-level documents
        with same generator (and even in that case this is optional thing to do).
        As a result usually only {@link SmileFactory} calls this method.
        """
        last = HEADER_BYTE_4
        if self.share_keys:
            last |= HEADER_BIT_HAS_SHARED_NAMES
        if self.share_values:
            last |= HEADER_BIT_HAS_SHARED_STRING_VALUES
        if not self.encode_as_7bit:
            last |= HEADER_BIT_HAS_RAW_BINARY
        self.write_bytes(HEADER_BYTE_1, HEADER_BYTE_2, HEADER_BYTE_3, int(last))

    def write_end_marker(self):
        """Write optional end marker (BYTE_MARKER_END_OF_CONTENT - 0xFF)"""
        self.write_byte(BYTE_MARKER_END_OF_CONTENT)

    def write_field_name(self, name):
        """
        Write Field Name
        :param str name: Name
        """
        str_len = len(name)
        if not name:
            return self.write_byte(TOKEN_KEY_EMPTY_STRING)

        # First: is it something we can share?
        if self.share_keys:
            ix = self._find_seen_name(name)
            if ix >= 0:
                return self.write_shared_name_reference(ix)

        if str_len > MAX_SHORT_NAME_UNICODE_BYTES:
            #  can not be a 'short' String; off-line (rare case)
            return self.write_non_short_field_name(name)
        if isinstance(name, unicode):
            utf_8_name = name.encode('utf-8')
            if len(utf_8_name) == str_len:
                return self.write_field_name(utf_8_name)

            if len(utf_8_name) <= MAX_SHORT_NAME_UNICODE_BYTES:
                #  yes, is short indeed
                #  note: since 2 is smaller allowed length, offset differs from one used for
                type_token = int(((TOKEN_PREFIX_KEY_UNICODE - 2) + len(utf_8_name)))
                self.write_bytes(type_token, utf_8_name)
            else:
                self.write_bytes(TOKEN_KEY_LONG_STRING, utf_8_name, BYTE_MARKER_END_OF_STRING)
            if self.share_keys:
                self._add_seen_name(utf_8_name)
        else:  # if isinstance(name, str):
            if str_len <= MAX_SHORT_NAME_ASCII_BYTES:
                self.write_bytes(int(((TOKEN_PREFIX_KEY_ASCII - 1) + str_len)), name)
            else:
                self.write_bytes(TOKEN_KEY_LONG_STRING, name, BYTE_MARKER_END_OF_STRING)
            if self.share_keys:
                self._add_seen_name(name)

    def write_non_short_field_name(self, name):
        """
        Write nonshort field name

        :param basestring name: Name
        """
        self.write_byte(TOKEN_KEY_LONG_STRING)
        try:
            utf_8_name = name.encode('utf-8')
        except UnicodeEncodeError:
            utf_8_name = name
        self.write_bytes(utf_8_name)
        if self.share_keys:
            self._add_seen_name(name)
        self.write_byte(BYTE_MARKER_END_OF_STRING)

    def write_string_field(self, name, value):
        """
        Write String Field

        :param str name: Name
        :param str value: Value
        """
        self.write_field_name(name)
        self.write_string(value)

    def write_string(self, text):
        """
        Write String

        :param str text: String text
        """
        if text is None:
            return self.write_null()
        if not text:
            return self.write_byte(TOKEN_LITERAL_EMPTY_STRING)
        # Longer string handling off-lined
        if len(text) > MAX_SHARED_STRING_LENGTH_BYTES:
            return self.write_non_shared_string(text)

        # Then: is it something we can share?
        if self.share_values:
            ix = self._find_seen_string_value(text)
            if ix >= 0:
                return self.write_shared_string_value_reference(ix)

        if isinstance(text, unicode):
            utf_8_text = text.encode('utf-8')
            if len(utf_8_text) <= MAX_SHORT_VALUE_STRING_BYTES:
                if self.share_values:
                    self._add_seen_string_value(text)
                if len(utf_8_text) == len(text):
                    self.write_byte(int((TOKEN_PREFIX_TINY_ASCII - 1) + len(utf_8_text)))
                else:
                    self.write_byte(int((TOKEN_PREFIX_TINY_UNICODE - 2) + len(utf_8_text)))
                self.write_bytes(utf_8_text)
            else:
                if len(utf_8_text) == len(text):
                    self.write_byte(TOKEN_BYTE_LONG_STRING_ASCII)
                else:
                    self.write_byte(TOKEN_MISC_LONG_TEXT_UNICODE)
                self.write_bytes(utf_8_text, BYTE_MARKER_END_OF_STRING)
        else:
            if len(text) <= MAX_SHORT_VALUE_STRING_BYTES:
                if self.share_values:
                    self._add_seen_string_value(text)
                self.write_bytes(int((TOKEN_PREFIX_TINY_ASCII - 1) + len(text)), text)
            else:
                self.write_bytes(TOKEN_BYTE_LONG_STRING_ASCII, text, BYTE_MARKER_END_OF_STRING)

    def write_start_array(self):
        """Write start array token"""
        self.write_byte(TOKEN_LITERAL_START_ARRAY)

    def write_end_array(self):
        """Write end array token"""
        self.write_byte(TOKEN_LITERAL_END_ARRAY)

    def write_start_object(self):
        """Write start object token"""
        self.write_byte(TOKEN_LITERAL_START_OBJECT)

    def write_end_object(self):
        """Write end object token"""
        self.write_byte(TOKEN_LITERAL_END_OBJECT)

    def write_shared_name_reference(self, ix):
        """
        Write Shared Name Ref

        :param int ix: Index
        """
        if ix >= len(self.shared_keys)-1:
            raise ValueError(
                'Trying to write shared name with index {} but have only seen {}!'.format(
                    ix, len(self.shared_keys)))
        if ix < 64:
            self.write_byte(int((TOKEN_PREFIX_KEY_SHARED_SHORT + ix)))
        else:
            self.write_bytes((int((TOKEN_PREFIX_KEY_SHARED_LONG + (ix >> 8)))), int(ix))

    def write_shared_string_value_reference(self, ix):
        """
        Write shared string

        :param int ix: Index
        """
        if ix > len(self.shared_values)-1:
            raise IllegalArgumentException(
                'Internal error: trying to write shared String value with index {}; but have '
                'only seen {} so far!'.format(ix, len(self.shared_values)))
        if ix < 31:
            #  add 1, as byte 0 is omitted
            self.write_byte(TOKEN_PREFIX_SHARED_STRING_SHORT + 1 + ix)
        else:
            self.write_bytes(TOKEN_PREFIX_SHARED_STRING_LONG + (ix >> 8), int(ix))

    def write_non_shared_string(self, text):
        """
        Helper method called to handle cases where String value to write is known to be long
        enough not to be shareable.

        :param str text: Text
        """
        if isinstance(text, unicode):
            utf_8_text = text.encode('utf-8')
            if len(utf_8_text) <= MAX_SHORT_VALUE_STRING_BYTES:
                if len(utf_8_text) == len(text):
                    self.write_byte(int((TOKEN_PREFIX_TINY_ASCII - 1) + len(utf_8_text)))
                else:
                    self.write_byte(int((TOKEN_PREFIX_TINY_UNICODE - 2) + len(utf_8_text)))
                self.write_bytes(utf_8_text)
            else:
                if len(utf_8_text) == len(text):
                    self.write_byte(TOKEN_MISC_LONG_TEXT_ASCII)
                else:
                    self.write_byte(TOKEN_MISC_LONG_TEXT_UNICODE)
                self.write_bytes(utf_8_text, BYTE_MARKER_END_OF_STRING)
        else:
            if len(text) <= MAX_SHORT_VALUE_STRING_BYTES:
                self.write_bytes(int((TOKEN_PREFIX_TINY_ASCII - 1) + len(text)), text)
            else:
                self.write_bytes(TOKEN_MISC_LONG_TEXT_ASCII, text, BYTE_MARKER_END_OF_STRING)

    def write_binary(self, data):
        """
        Write Data

        :param data: Data
        """
        if data is None:
            return self.write_null()
        if self.encode_as_7bit:
            self.write_byte(TOKEN_MISC_BINARY_7BIT)
            self.write_7bit_binary(data)
        else:
            self.write_byte(TOKEN_MISC_BINARY_RAW)
            self.write_positive_vint(len(data))
            self.write_bytes(data)

    def write_true(self):
        """Write True Value"""
        self.write_byte(TOKEN_LITERAL_TRUE)

    def write_false(self):
        """Write True Value"""
        self.write_byte(TOKEN_LITERAL_FALSE)

    def write_boolean(self, state):
        """
        Write Boolean

        :param bool state: Bool state
        """
        self.write_byte(state and TOKEN_LITERAL_TRUE or TOKEN_LITERAL_FALSE)

    def write_null(self):
        """ generated source for method writeNull """
        self.write_byte(TOKEN_LITERAL_NULL)

    def write_number(self, i):
        """
        Write Numner

        :param int|long|float|str i: number
        """
        if isinstance(i, int):
            #  First things first: let's zigzag encode number
            i = util.zigzag_encode(i)
            #  tiny (single byte) or small (type + 6-bit value) number?
            if 0x3F >= i >= 0:
                if i <= 0x1F:
                    self.write_byte(int((TOKEN_PREFIX_SMALL_INT + i)))
                    return
                #  nope, just small, 2 bytes (type, 1-byte zigzag value) for 6 bit value
                self.write_bytes(TOKEN_BYTE_INT_32, int((0x80 + i)))
                return
            #  Ok: let's find minimal representation then
            b0 = int((0x80 + (i & 0x3F)))
            i >>= 6
            if i <= 0x7F:
                #  13 bits is enough (== 3 byte total encoding)
                self.write_bytes(TOKEN_BYTE_INT_32, int(i), b0)
                return
            b1 = int((i & 0x7F))
            i >>= 7
            if i <= 0x7F:
                self.write_bytes(TOKEN_BYTE_INT_32, int(i), b1, b0)
                return
            b2 = int((i & 0x7F))
            i >>= 7
            if i <= 0x7F:
                self.write_bytes(TOKEN_BYTE_INT_32, int(i), b2, b1, b0)
                return
            #  no, need all 5 bytes
            b3 = int((i & 0x7F))
            self.write_bytes(TOKEN_BYTE_INT_32, int((i >> 7)), b3, b2, b1, b0)
        elif isinstance(i, long):
            #  First: maybe 32 bits is enough?
            if MAX_INT_AS_LONG >= i >= MIN_INT_AS_LONG:
                return self.write_number(int(i))

            # Then let's zigzag encode it
            l = util.zigzag_encode(i)
            #  Ok, well, we do know that 5 lowest-significant bytes are needed
            i = int(l)
            #  4 can be extracted from lower int
            b0 = int((0x80 + (i & 0x3F)))
            #  sign bit set in the last byte
            b1 = int(((i >> 6) & 0x7F))
            b2 = int(((i >> 13) & 0x7F))
            b3 = int(((i >> 20) & 0x7F))
            #  fifth one is split between ints:
            l = bsr(l, 27)
            b4 = int(((int(l)) & 0x7F))
            #  which may be enough?
            i = int((l >> 7))
            if i == 0:
                self.write_bytes(TOKEN_BYTE_INT_64, b4, b3, b2, b1, b0)
                return
            if i <= 0x7F:
                self.write_bytes(TOKEN_BYTE_INT_64, int(i), b4, b3, b2, b1, b0)
                return
            b5 = int((i & 0x7F))
            i >>= 7
            if i <= 0x7F:
                self.write_bytes(TOKEN_BYTE_INT_64, int(i), b5, b4, b3, b2, b1, b0)
                return
            b6 = int((i & 0x7F))
            i >>= 7
            if i <= 0x7F:
                self.write_bytes(TOKEN_BYTE_INT_64, int(i), b6, b5, b4, b3, b2, b1, b0)
                return
            b7 = int((i & 0x7F))
            i >>= 7
            if i <= 0x7F:
                self.write_bytes(TOKEN_BYTE_INT_64, int(i), b7, b6, b5, b4, b3, b2, b1, b0)
                return
            b8 = int((i & 0x7F))
            i >>= 7
            #  must be done, with 10 bytes! (9 * 7 + 6 == 69 bits; only need 63)
            self.write_bytes(TOKEN_BYTE_INT_64, int(i), b8, b7, b6, b5, b4, b3, b2, b1, b0)

        elif isinstance(i, basestring):
            if not i:
                self.write_null()
                return
            neg = i.startswith('-')
            i = i.strip('-')
            if i.isdigit():
                self.write_integral_number(i, neg)
            else:
                self.write_decimal_number(i)
        elif isinstance(i, (float, decimal.Decimal)):
            if isinstance(i, decimal.Decimal) and isinstance(int(float(i)), long):
                self.write_byte(TOKEN_BYTE_BIG_DECIMAL)
                scale = i.as_tuple().exponent
                self.write_signed_vint(scale)
                self.write_7bit_binary(bytearray(str(i.to_integral_value())))
            else:
                i = float(i)
                try:
                    i = util.float_to_bits(i)
                    self.write_byte(TOKEN_BYTE_FLOAT_32)
                    self.write_byte(int(i & 0x7F))
                    for _ in xrange(4):
                        i >>= 7
                        self.write_byte(int(i & 0x7F))
                except struct.error:
                    i = util.float_to_raw_long_bits(i)
                    self.write_byte(TOKEN_BYTE_FLOAT_64)
                    self.write_byte(int(i & 0x7F))
                    for _ in xrange(9):
                        i >>= 7
                        self.write_byte(int(i & 0x7F))

    def write_big_number(self, i):
        """
        Write Big Number

        :param i: Big Number
        """
        if i is None:
            return self.write_null()
        self.write_byte(TOKEN_BYTE_BIG_INTEGER)
        self.write_7bit_binary(bytearray(str(i)))

    def write_integral_number(self, num, neg=False):
        """
        Write Int

        :param str num: String of an integral number
        :param bool neg: Is the value negative
        """
        if num is None:
            return self.write_null()
        num_len = len(num)
        if neg:
            num_len -= 1
        # try:
        if num_len <= 9:
            self.write_number(int(num))
        elif num_len <= 18:
            self.write_number(long(num))
        else:
            self.write_big_number(num)

    def write_decimal_number(self, num):
        """
        Write decimal

        :param str num: String of a decimal number
        """
        if num is None:
            return self.write_null()
        self.write_number(decimal.Decimal(num))

    def write_byte(self, c):
        """
        Write byte

        :param int|long|float|basestring c: byte
        """
        if isinstance(c, basestring):
            if isinstance(c, unicode):
                c = c.encode('utf-8')
        elif isinstance(c, float):
            c = str(c)
        elif isinstance(c, (int, long)):
            try:
                c = chr(c)
            except ValueError:
                c = str(c)
        else:
            raise ValueError('Invalid type for param "c"!')
        self.output.extend(c)

    def write_bytes(self, *args):
        """
        Write bytes

        :param args: args
        """
        map(self.write_byte, args)

    def write_positive_vint(self, i):
        """
        Helper method for writing a 32-bit positive (really 31-bit then) value.
        Value is NOT zigzag encoded (since there is no sign bit to worry about)

        :param int i: Int
        """
        #  At most 5 bytes (4 * 7 + 6 bits == 34 bits)
        b0 = int((0x80 + (i & 0x3F)))
        i >>= 6
        if i <= 0x7F:
            #  6 or 13 bits is enough (== 2 or 3 byte total encoding)
            if i > 0:
                self.write_byte(int(i))
            self.write_byte(b0)
            return
        b1 = int((i & 0x7F))
        i >>= 7
        if i <= 0x7F:
            self.write_bytes(int(i), b1, b0)
        else:
            b2 = int((i & 0x7F))
            i >>= 7
            if i <= 0x7F:
                self.write_bytes(int(i), b2, b1, b0)
            else:
                b3 = int((i & 0x7F))
                self.write_bytes(int((i >> 7)), b3, b2, b1, b0)

    def write_signed_vint(self, i):
        """
        Helper method for writing 32-bit signed value, using
        "zig zag encoding" (see protocol buffers for explanation -- basically,
        sign bit is moved as LSB, rest of value shifted left by one)
        coupled with basic variable length encoding

        :param int i: Signed int
        """
        self.write_positive_vint(util.zigzag_encode(i))

    def write_7bit_binary(self, data, offset=0):
        l = len(data)
        self.write_positive_vint(l)
        while l >= 7:
            i = data[offset]
            offset += 1
            for x in xrange(1, 7):
                self.write_byte(int(((i >> x) & 0x7F)))
                i = (i << 8) | (data[offset + x] & 0xFF)
                offset += 1
            self.write_bytes(int(((i >> 7) & 0x7F)), int((i & 0x7F)))
            l -= 7
        #  and then partial piece, if any
        if l > 0:
            i = data[offset]
            offset += 1
            self.write_byte(int(((i >> 1) & 0x7F)))
            if l > 1:
                i = ((i & 0x01) << 8) | (data[offset] & 0xFF)
                offset += 1

                #  2nd
                self.write_byte(int(((i >> 2) & 0x7F)))
                if l > 2:
                    i = ((i & 0x03) << 8) | (data[offset] & 0xFF)
                    offset += 1
                    #  3rd
                    self.write_byte(int(((i >> 3) & 0x7F)))
                    if l > 3:
                        i = ((i & 0x07) << 8) | (data[offset] & 0xFF)
                        offset += 1
                        #  4th
                        self.write_byte(int(((i >> 4) & 0x7F)))
                        if l > 4:
                            i = ((i & 0x0F) << 8) | (data[offset] & 0xFF)
                            offset += 1
                            #  5th
                            self.write_byte(int(((i >> 5) & 0x7F)))
                            if l > 5:
                                i = ((i & 0x1F) << 8) | (data[offset] & 0xFF)
                                offset += 1
                                #  6th
                                self.write_byte(int(((i >> 6) & 0x7F)))
                                self.write_byte(int((i & 0x3F)))
                                #  last 6 bits
                            else:
                                self.write_byte(int((i & 0x1F)))
                                #  last 5 bits
                        else:
                            self.write_byte(int((i & 0x0F)))
                            #  last 4 bits
                    else:
                        self.write_byte(int((i & 0x07)))
                        #  last 3 bits
                else:
                    self.write_byte(int((i & 0x03)))
                    #  last 2 bits
            else:
                self.write_byte(int((i & 0x01)))
                #  last bit

    def _find_seen_name(self, name):
        n_hash = util.hash_string(name)
        try:
            head = self.shared_keys[n_hash & (len(self.shared_keys) - 1)]
        except IndexError:
            return -1
        if head is None:
            return -1

        if head.value is name:
            return head.index

        node = head
        while node:
            if node.value is name:
                return node.index
            node = node.next
        node = head
        while node:
            if node.value == name and util.hash_string(node.value) == n_hash:
                return node.index
            node = node.next

    def _add_seen_name(self, name):
        # if self.seen_name_count == len(self.shared_keys):
        if self.shared_keys:
            if len(self.shared_keys) == MAX_SHARED_NAMES:
                # self.seen_name_count = 0
                self.shared_keys = [None] * len(self.shared_keys)
            else:
                old = copy.copy(self.shared_keys)
                self.shared_keys = [None] * MAX_SHARED_NAMES
                mask = MAX_SHARED_NAMES - 1
                for node in old:
                    while node:
                        ix = util.hash_string(node.value) & mask
                        next_node = node.next
                        try:
                            node.next = self.shared_keys[ix]
                        except IndexError:
                            node.next = None
                        self.shared_keys[ix] = node
                        node = next_node
            # ref = self.seen_name_count
            if _is_valid_back_ref(len(self.shared_keys)):
                ix = util.hash_string(name) & (len(self.shared_keys) - 1)
                self.shared_keys[ix] = SharedStringNode(name, ref, self.shared_keys[ix])
            # self.seen_name_count = ref + 1

    def _find_seen_string_value(self, text):
        hash_ = util.hash_string(text)
        try:
            head = self.shared_values[hash_ & (len(self.shared_values) - 1)]
        except IndexError:
            return -1
        if head is None:
            return -1
        node = head
        while node:
            if node.value is text:
                return node.index
            node = node.next
        node = head
        while node:
            if util.hash_string(node.value) == hash_ and node.value == text:
                return node.index
            node = node.next

    def _add_seen_string_value(self, text):
        # if self.seen_string_count == len(self.shared_values):
        if self.shared_values:
            if self.seen_string_count == MAX_SHARED_STRING_VALUES:
                self.seen_string_count = 0
                self.shared_values = [None] * len(self.shared_values)
            else:
                old = copy.copy(self.shared_values)
                self.shared_values = [None] * MAX_SHARED_STRING_VALUES
                mask = MAX_SHARED_STRING_VALUES - 1
                for node in old:
                    while node:
                        ix = util.hash_string(node.value) & mask
                        next_node = node.next
                        try:
                            node.next = self.shared_values[ix]
                        except IndexError:
                            node.next = None
                        self.shared_values[ix] = node
                        node = next_node
            # ref = self.seen_string_count
            if _is_valid_back_ref(len(self.shared_values)):
                ix = util.hash_string(text) & (len(self.shared_values) - 1)
                self.shared_values[ix] = SharedStringNode(text, ref, self.shared_values[ix])
            # self.seen_string_count = ref + 1


def _is_valid_back_ref(index):
    """
    Helper method used to ensure that we do not use back-reference values
    that would produce illegal byte sequences (ones with byte 0xFE or 0xFF).
    Note that we do not try to avoid null byte (0x00) by default, although
    it would be technically possible as well.

    :param int index: Index
    :returns: Valid back ref
    :rtype: bool
    """
    return (index & 0xFF) < 0xFE


def encode(py_obj, header=True, ender=False, shared_keys=True, shared_vals=True, bin_7bit=True):
    """
    SMILE Encode object

    :param list|dict py_obj: The object to be encoded
    :param bool header: (optional - Default: `True`)
    :param bool ender: (optional - Default: `False`)
    :param bool bin_7bit: (optional - Default: `True`) Encode raw data as 7-bit
    :param bool shared_keys: (optional - Default: `True`) Shared Key String References
    :param bool shared_vals: (optional - Default: `True`) Shared Value String References
    :returns: SMILE encoded data
    :rtype: str
    """
    if isinstance(py_obj, (tuple, set)):
        py_obj = list(py_obj)
    elif not isinstance(py_obj, (list, dict)):
        raise ValueError('Invalid type for "obj" paramater.  Must be list or tuple')

    sg = SmileGenerator(shared_keys, shared_vals, bin_7bit)
    if header:
        sg.write_header()

    def _floatstr(f):
        """
        Convert a Python float into a JSON float string

        :param float f: Floating point number
        :returns: JSON String representation of the float
        :rtype: str
        """
        _inf = float('inf')
        if f != f:
            text = 'NaN'
        elif f == _inf:
            text = 'Infinity'
        elif f == -_inf:
            text = '-Infinity'
        else:
            return repr(f)
        return text

    def _iterencode(obj):
        if isinstance(obj, basestring):
            sg.write_string(obj)
        elif obj is None:
            sg.write_null()
        elif obj is True:
            sg.write_true()
        elif obj is False:
            sg.write_false()
        elif isinstance(obj, float):
            sg.write_number(obj)
        elif isinstance(obj, (int, long)):
            sg.write_number(obj)
        elif isinstance(obj, (list, tuple, set)):
            sg.write_start_array()
            for v in list(obj):
                _iterencode(v)
            sg.write_end_array()
        elif isinstance(obj, dict):
            sg.write_start_object()
            for key, val in obj.iteritems():
                if key is True:
                    key = 'true'
                elif key is False:
                    key = 'false'
                elif key is None:
                    key = 'null'
                elif isinstance(key, (int, long)):
                    key = str(key)
                elif isinstance(key, float):
                    key = _floatstr(key)
                elif not isinstance(key, basestring):
                    raise TypeError('Key ' + repr(key) + ' is not a string')
                sg.write_field_name(key)
                _iterencode(val)
            sg.write_end_object()
        else:
            _iterencode(obj)
    _iterencode(py_obj)
    if ender:
        sg.write_end_marker()
    return str(sg.output)


if __name__ == '__main__':
    a = ':)\n\x03\xfa\x80a@1\x80c\xf8\xc6\xf9\x80b\xc4\x80e(fL\x19\x04\x04\x80d\xc1\xfb'
    b = encode({'a': '1', 'b': 2, 'c': [3], 'd': -1, 'e': 4.20})
    if a != b:
        print repr(a)
        print repr(b)

    a = ':)\n\x03\xfa\x80a\xfa\x80b\xfa\x80c\xfa\x80d\xf8@e\xf9\xfb\xfb\xfb\xfb'
    b = encode({'a': {'b': {'c': {'d': ['e']}}}})
    if a != b:
        print repr(a)
        print repr(b)
