"""Conversion between decimal numbers and an 8-bit floating-point format.

Bit layout (the format taught in Brookshear's "Computer Science: An Overview"):

    s eee mmmm
    |  |   +--- mantissa: 4 bits, radix point on the left (0.mmmm)
    |  +------- exponent: 3 bits in excess-4 notation (range -4 to 3)
    +---------- sign:     0 = positive, 1 = negative

    value = (-1)^s * 0.mmmm (base 2) * 2^(eee - 4)

All arithmetic uses fractions.Fraction, so results are exact and free of
floating-point rounding errors.
"""

from dataclasses import dataclass
from fractions import Fraction
from typing import Union

TOTAL_BITS = 8
EXPONENT_BITS = 3
MANTISSA_BITS = 4
EXPONENT_BIAS = 4                          # excess-4 notation
MIN_EXPONENT = -EXPONENT_BIAS              # -4
MAX_EXPONENT = 2**EXPONENT_BITS - 1 - EXPONENT_BIAS   # 3

MANTISSA_SCALE = 2**MANTISSA_BITS          # 16
MAX_VALUE = Fraction(MANTISSA_SCALE - 1, MANTISSA_SCALE) * 2**MAX_EXPONENT   # 7.5
MIN_POSITIVE = Fraction(1, 2) * Fraction(2) ** MIN_EXPONENT                  # 1/32


class ConversionError(ValueError):
    """Raised for invalid input or values the format cannot represent."""


@dataclass(frozen=True)
class Encoding:
    """Result of converting a number to the 8-bit format."""

    bits: str            # e.g. "01101011"
    stored: Fraction     # the value the bits actually represent
    original: Fraction   # the value that was requested

    @property
    def exact(self) -> bool:
        return self.stored == self.original

    @property
    def truncation_error(self) -> Fraction:
        return self.original - self.stored


def _exponent_bits(exponent: int) -> str:
    return format(exponent + EXPONENT_BIAS, f"0{EXPONENT_BITS}b")


def decode(bits: str) -> Fraction:
    """Convert an 8-bit pattern such as "01101011" to its exact value (11/4)."""
    bits = bits.replace(" ", "")
    if len(bits) != TOTAL_BITS or set(bits) - {"0", "1"}:
        raise ConversionError("Enter exactly 8 bits, using only 0 and 1.")

    sign = -1 if bits[0] == "1" else 1
    exponent = int(bits[1:1 + EXPONENT_BITS], 2) - EXPONENT_BIAS
    mantissa = Fraction(int(bits[1 + EXPONENT_BITS:], 2), MANTISSA_SCALE)
    return sign * mantissa * Fraction(2) ** exponent


def parse_number(text: str) -> Fraction:
    """Parse user input such as "2.75", "-0.375", "3/8" or "1e-2" exactly."""
    cleaned = text.strip().replace(",", ".")
    try:
        return Fraction(cleaned)
    except (ValueError, ZeroDivisionError):
        raise ConversionError(
            "Enter a number such as 2.75, -0.375 or 3/8."
        ) from None


def encode(value: Union[str, int, Fraction]) -> Encoding:
    """Convert a number to the 8-bit format.

    The number is normalized (the first mantissa bit is always 1) and any
    bits that do not fit in the 4-bit mantissa are truncated, as in the
    textbook format. Raises ConversionError on overflow or underflow.
    """
    original = parse_number(value) if isinstance(value, str) else Fraction(value)

    if original == 0:
        return Encoding("0" * TOTAL_BITS, Fraction(0), original)

    sign_bit = "1" if original < 0 else "0"
    magnitude = abs(original)

    # Normalize: find the exponent so that 1/2 <= magnitude / 2^exponent < 1.
    exponent = 0
    normalized = magnitude
    while normalized >= 1:
        normalized /= 2
        exponent += 1
    while normalized < Fraction(1, 2):
        normalized *= 2
        exponent -= 1

    if exponent > MAX_EXPONENT:
        raise ConversionError(
            f"Overflow: the largest representable magnitude is {format_value(MAX_VALUE)}."
        )
    if exponent < MIN_EXPONENT:
        raise ConversionError(
            f"Underflow: the smallest representable magnitude is {format_value(MIN_POSITIVE)}."
        )

    mantissa = int(normalized * MANTISSA_SCALE)          # truncates extra bits
    bits = sign_bit + _exponent_bits(exponent) + format(mantissa, f"0{MANTISSA_BITS}b")
    return Encoding(bits, decode(bits), original)


def describe(bits: str) -> str:
    """Human-readable breakdown, e.g. "+ 0.1011 x 2^2"."""
    bits = bits.replace(" ", "")
    decode(bits)  # validates
    sign = "-" if bits[0] == "1" else "+"
    exponent = int(bits[1:4], 2) - EXPONENT_BIAS
    return f"{sign} 0.{bits[4:]} x 2^{exponent}"


def format_value(value: Fraction) -> str:
    """Show a value as a fraction and a decimal, e.g. "11/4 = 2.75"."""
    if value.denominator == 1:
        return str(value.numerator)
    # Every value in this format is a small dyadic fraction, so float is exact.
    return f"{value} = {float(value)!r}"
