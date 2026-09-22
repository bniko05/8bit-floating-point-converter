from fractions import Fraction

import pytest

from converter import (
    MAX_VALUE,
    MIN_POSITIVE,
    ConversionError,
    decode,
    describe,
    encode,
    format_value,
)

ALL_PATTERNS = [format(i, "08b") for i in range(256)]


@pytest.mark.parametrize(
    "bits, expected",
    [
        ("01101011", Fraction(11, 4)),     # textbook example: 2 3/4
        ("00101100", Fraction(3, 16)),
        ("10111100", Fraction(-3, 8)),
        ("01111111", Fraction(15, 2)),     # largest value
        ("00001000", Fraction(1, 32)),     # smallest normalized value
        ("0110 1011", Fraction(11, 4)),    # spaces are allowed
        ("00000000", Fraction(0)),
    ],
)
def test_decode_known_values(bits, expected):
    assert decode(bits) == expected


@pytest.mark.parametrize("bits", ["0110", "011010110", "51101011", "0110201a", ""])
def test_decode_rejects_invalid_input(bits):
    with pytest.raises(ConversionError):
        decode(bits)


@pytest.mark.parametrize(
    "value, expected_bits",
    [
        ("2.75", "01101011"),
        ("1", "01011000"),        # was encoded as 0 in the original version
        ("2", "01101000"),        # was encoded as 0 in the original version
        ("4", "01111000"),        # was encoded as 0 in the original version
        ("0.5", "01001000"),
        ("0.1875", "00101100"),   # must be normalized, not 01000011
        ("0.03125", "00001000"),  # crashed in the original version
        ("-0.375", "10111100"),
        ("7.5", "01111111"),
        ("3/8", "00111100"),
        ("0", "00000000"),
    ],
)
def test_encode_exact_values(value, expected_bits):
    result = encode(value)
    assert result.bits == expected_bits
    assert result.exact


def test_encode_truncates_like_the_textbook():
    # 2 5/8 = 10.101 -> 0.10101 x 2^2 -> the last bit does not fit
    result = encode("2.625")
    assert result.bits == "01101010"
    assert result.stored == Fraction(5, 2)
    assert not result.exact
    assert result.truncation_error == Fraction(1, 8)


@pytest.mark.parametrize("value", ["8", "10", "-100", "7.9999"])
def test_encode_overflow(value):
    if value == "7.9999":
        # just below 8 still fits (truncated to 7.5)
        assert encode(value).stored == MAX_VALUE
        return
    with pytest.raises(ConversionError, match="Overflow"):
        encode(value)


@pytest.mark.parametrize("value", ["0.01", "-0.03", "1/64"])
def test_encode_underflow(value):
    with pytest.raises(ConversionError, match="Underflow"):
        encode(value)


@pytest.mark.parametrize("value", ["abc", "", "1/0", "2..5"])
def test_encode_rejects_invalid_input(value):
    with pytest.raises(ConversionError):
        encode(value)


@pytest.mark.parametrize("bits", ALL_PATTERNS)
def test_every_pattern_round_trips(bits):
    value = decode(bits)
    if value == 0 or abs(value) < MIN_POSITIVE:
        return  # zeros and unnormalized tiny values have no normalized form
    result = encode(value)
    assert result.exact
    assert decode(result.bits) == value
    if bits[4] == "1":  # already normalized -> identical bit pattern
        assert result.bits == bits


def test_describe_and_format():
    assert describe("01101011") == "+ 0.1011 x 2^2"
    assert format_value(Fraction(11, 4)) == "11/4 = 2.75"
    assert format_value(Fraction(-3)) == "-3"
