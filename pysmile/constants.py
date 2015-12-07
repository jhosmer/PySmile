"""
Constants
"""

import sys

#
#
#  Thresholds
#
# Encoding has special "short" forms for value Strings that can
# be represented by 64 bytes of UTF-8 or less.
#
MAX_SHORT_VALUE_STRING_BYTES = 64

#
# Encoding has special "short" forms for field names that can
# be represented by 64 bytes of UTF-8 or less.
#
MAX_SHORT_NAME_ASCII_BYTES = 64

#
# Maximum byte length for short non-ASCII names is slightly
# less due to having to reserve bytes 0xF8 and above (but
# we get one more as values 0 and 1 are not valid)
#
MAX_SHORT_NAME_UNICODE_BYTES = 56

#
# Longest back reference we use for field names is 10 bits; no point
# in keeping much more around
#
MAX_SHARED_NAMES = 1024

#
# Longest back reference we use for short shared String values is 10 bits,
# so up to (1 << 10) values to keep track of.
#
MAX_SHARED_STRING_VALUES = 1024

#
# Also: whereas we can refer to names of any length, we will only consider
# text values that are considered "tiny" or "short" (ones encoded with
# length prefix); this value thereby has to be maximum length of Strings
# that can be encoded as such.
#
MAX_SHARED_STRING_LENGTH_BYTES = 65

#
# And to make encoding logic tight and simple, we can always
# require that output buffer has this amount of space
# available before encoding possibly short String (3 bytes since
# longest UTF-8 encoded Java char is 3 bytes).
# Two extra bytes need to be reserved as well; first for token indicator,
# and second for terminating null byte (in case it's not a short String after all)
#
MIN_BUFFER_FOR_POSSIBLE_SHORT_STRING = 1 + (3 * 65)

#
#
#  Byte markers
#
# We need a byte marker to denote end of variable-length Strings. Although
# null byte is commonly used, let's try to avoid using it since it can't
# be embedded in Web Sockets content (similarly, 0xFF can't). There are
# multiple candidates for bytes UTF-8 can not have; 0xFC is chosen to
# allow reasonable ordering (highest values meaning most significant
# framing function; 0xFF being end-of-content and so on)
#
INT_MARKER_END_OF_STRING = 0xFC
BYTE_MARKER_END_OF_STRING = INT_MARKER_END_OF_STRING

#
# In addition we can use a marker to allow simple framing; splitting
# of physical data (like file) into distinct logical sections like
# JSON documents. 0xFF makes sense here since it is also used
# as end marker for Web Sockets.
#
BYTE_MARKER_END_OF_CONTENT = 0xFF

#
#
#  Format header: put smile on your data...
#
# First byte of data header (0x3A)
#
HEADER_BYTE_1 = ':'

#
# Second byte of data header (0x29)
#
HEADER_BYTE_2 = ')'

#
# Third byte of data header
#
HEADER_BYTE_3 = '\n'

NULL_BIT = 0x0
#
# Current version consists of four zero bits (nibble)
#
HEADER_VERSION_0 = NULL_BIT

HEADER_BIT_VERSION = 0xF0

#
# Fourth byte of data header; contains version nibble, may
# have flags
#
HEADER_BYTE_4 = (HEADER_VERSION_0 << 4)

#
# Indicator bit that indicates whether encoded content may
# have Shared names (back references to recently encoded field
# names). If no header available, must be
# processed as if this was set to true.
# If (and only if) header exists, and value is 0, can parser
# omit storing of seen names, as it is guaranteed that no back
# references exist.
#
HEADER_BIT_HAS_SHARED_NAMES = 0x01

#
# Indicator bit that indicates whether encoded content may
# have shared String values (back references to recently encoded
# 'short' String values, where short is defined as 64 bytes or less).
# If no header available, can be assumed to be 0 (false).
# If header exists, and bit value is 1, parsers has to store up
# to 1024 most recently seen distinct short String values.
#
HEADER_BIT_HAS_SHARED_STRING_VALUES = 0x02

#
# Indicator bit that indicates whether encoded content may
# contain raw (unquoted) binary values.
# If no header available, can be assumed to be 0 (false).
# If header exists, and bit value is 1, parser can not assume that
# specific byte values always have default meaning (specifically,
# content end marker 0xFF and header signature can be contained
# in binary values)
#      *<p>
# Note that this bit being true does not automatically mean that
# such raw binary content indeed exists; just that it may exist.
# This because header is written before any binary data may be
# written.
#
HEADER_BIT_HAS_RAW_BINARY = 0x04

#
#
#  Type prefixes: 3 MSB of token byte
#
#
TOKEN_PREFIX_INTEGER = 0x24
TOKEN_PREFIX_FP = 0x28

#  Shared strings are back references for last 63 short (< 64 byte) string values
#  NOTE: 0x00 is reserved, not used with current version (may be used in future)
TOKEN_PREFIX_SHARED_STRING_SHORT = 0x00

#  literals are put between 0x20 and 0x3F to reserve markers (smiley), along with ints/doubles
# public final static int TOKEN_PREFIX_MISC_NUMBERS = 0x20;
TOKEN_PREFIX_SHARED_STRING_LONG = 0xEC
TOKEN_PREFIX_TINY_ASCII = 0x40
TOKEN_PREFIX_SMALL_ASCII = 0x60
TOKEN_PREFIX_TINY_UNICODE = 0x80
TOKEN_PREFIX_SHORT_UNICODE = 0xA0

#  Small ints are 4-bit (-16 to +15) integer constants
TOKEN_PREFIX_SMALL_INT = 0xC0

#  And misc types have empty at the end too, to reserve 0xF8 - 0xFF
TOKEN_PREFIX_MISC_OTHER = 0xE0

#
#
#  Token literals, normal mode
# First, non-structured literals
TOKEN_LITERAL_EMPTY_STRING = 0x20
TOKEN_LITERAL_NULL = 0x21
TOKEN_LITERAL_FALSE = 0x22
TOKEN_LITERAL_TRUE = 0x23

#  And then structured literals
TOKEN_LITERAL_START_ARRAY = 0xF8
TOKEN_LITERAL_END_ARRAY = 0xF9
TOKEN_LITERAL_START_OBJECT = 0xFA
TOKEN_LITERAL_END_OBJECT = 0xFB

#
#
#  Subtype constants for misc text/binary types
#
#
INT_MISC_BINARY_7BIT = 0xE8
INT_MISC_BINARY_RAW = 0xFD

#
# Type (for misc, other) used for
# variable length UTF-8 encoded text, when it is known to only contain ASCII chars.
# Note: 2 LSB are reserved for future use; must be zeroes for now
#
TOKEN_MISC_LONG_TEXT_ASCII = 0xE0

#
# Type (for misc, other) used
# for variable length UTF-8 encoded text, when it is NOT known to only contain ASCII chars
# (which means it MAY have multi-byte characters)
# Note: 2 LSB are reserved for future use; must be zeroes for now
#
TOKEN_MISC_LONG_TEXT_UNICODE = 0xE4

#
# Type (for misc, other) used
# for "safe" (encoded by only using 7 LSB, giving 8/7 expansion ratio).
# This is usually done to ensure that certain bytes are never included
# in encoded data (like 0xFF)
# Note: 2 LSB are reserved for future use; must be zeroes for now
#
TOKEN_MISC_BINARY_7BIT = INT_MISC_BINARY_7BIT

#
# Raw binary data marker is specifically chosen as separate from
# other types, since it can have significant impact on framing
# (or rather fast scanning based on structure and framing markers).
#
TOKEN_MISC_BINARY_RAW = INT_MISC_BINARY_RAW

#
#
#  Modifiers for numeric entries
#
# Numeric subtype (2 LSB)
# indicating 32-bit integer (int)
#
TOKEN_MISC_INTEGER_32 = 0x00

#
# Numeric subtype (2 LSB)
# indicating 32-bit integer (long)
#
TOKEN_MISC_INTEGER_64 = 0x01

#
# Numeric subtype (2 LSB) for
# indicating {@link java.math.BigInteger} type.
#
TOKEN_MISC_INTEGER_BIG = 0x02

#  Note: type 3 (0xF3) reserved for future use
#
# Numeric subtype (2 LSB) for
# indicating 32-bit IEEE single precision floating point number.
#
TOKEN_MISC_FLOAT_32 = 0x00

#
# Numeric subtype (2 LSB)
# indicating 64-bit IEEE double precision floating point number.
#
TOKEN_MISC_FLOAT_64 = 0x01

#
# Numeric subtype (2 LSB) for
# indicating {@link java.math.BigDecimal} type.
#
TOKEN_MISC_FLOAT_BIG = 0x02

#  Note: type 3 (0xF7) reserved for future use
TOKEN_RESERVED = 0xF7
#
#  Token types for keys
#
# Let's use same code for empty key as for empty String value
#
TOKEN_KEY_EMPTY_STRING = 0x20
TOKEN_PREFIX_KEY_SHARED_LONG = 0x30
TOKEN_KEY_LONG_STRING = 0x34
TOKEN_PREFIX_KEY_SHARED_SHORT = 0x40
TOKEN_PREFIX_KEY_ASCII = 0x80
TOKEN_PREFIX_KEY_UNICODE = 0xC0


ID_NOT_AVAILABLE = -1
ID_NO_TOKEN = 0
ID_START_OBJECT = 1
ID_END_OBJECT = 2
ID_START_ARRAY = 3
ID_END_ARRAY = 4
ID_FIELD_NAME = 5
ID_STRING = 6
ID_NUMBER_INT = 7
ID_NUMBER_FLOAT = 8
ID_TRUE = 9
ID_FALSE = 10
ID_NULL = 11
ID_EMBEDDED_OBJECT = 12


MAX_SHAREABLE_STRING_LENGTH = 64
KEYS_BUFFER_SIZE = 1024
VALUES_BUFFER_SIZE = 1024
EIO = 5
ENOMEM = 12
MAX_ERROR_MSG_SIZE = 100
MAX_WBITS = 15


MIN_BUFFER_LENGTH = (3 * 256) + 2
TOKEN_BYTE_LONG_STRING_ASCII = TOKEN_MISC_LONG_TEXT_ASCII
TOKEN_BYTE_INT_32 = int((TOKEN_PREFIX_INTEGER + TOKEN_MISC_INTEGER_32))
TOKEN_BYTE_INT_64 = int((TOKEN_PREFIX_INTEGER + TOKEN_MISC_INTEGER_64))
TOKEN_BYTE_BIG_INTEGER = int((TOKEN_PREFIX_INTEGER + TOKEN_MISC_INTEGER_BIG))
TOKEN_BYTE_FLOAT_32 = int((TOKEN_PREFIX_FP | TOKEN_MISC_FLOAT_32))
TOKEN_BYTE_FLOAT_64 = int((TOKEN_PREFIX_FP | TOKEN_MISC_FLOAT_64))
TOKEN_BYTE_BIG_DECIMAL = int((TOKEN_PREFIX_FP | TOKEN_MISC_FLOAT_BIG))
MIN_INT_AS_LONG = long(-sys.maxint - 1)
MAX_INT_AS_LONG = long(sys.maxint)

DEFAULT_NAME_BUFFER_LENGTH = 64
DEFAULT_STRING_VALUE_BUFFER_LENGTH = 64
