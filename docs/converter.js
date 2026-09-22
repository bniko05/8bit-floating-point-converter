// Same algorithm as converter.py, using exact BigInt fractions.
// Format: s eee mmmm, value = (-1)^s * 0.mmmm (base 2) * 2^(eee - 4)
(function (root) {
  "use strict";

  const BIAS = 4, MIN_EXP = -4, MAX_EXP = 3, SCALE = 16n;

  function gcd(a, b) { a = a < 0n ? -a : a; while (b) [a, b] = [b, a % b]; return a; }

  function fraction(n, d) {
    const g = gcd(n, d) || 1n;
    return { n: n / g, d: d / g };
  }

  function formatValue({ n, d }) {
    if (d === 1n) return n.toString();
    return `${n}/${d} = ${Number(n) / Number(d)}`;   // dyadic, so exact
  }

  function decode(bits) {
    bits = bits.replace(/\s/g, "");
    if (!/^[01]{8}$/.test(bits)) throw new Error("Enter exactly 8 bits, using only 0 and 1.");
    const sign = bits[0] === "1" ? -1n : 1n;
    const exp = parseInt(bits.slice(1, 4), 2) - BIAS;
    const mant = BigInt(parseInt(bits.slice(4), 2));
    return exp >= 0 ? fraction(sign * mant * 2n ** BigInt(exp), SCALE)
                    : fraction(sign * mant, SCALE * 2n ** BigInt(-exp));
  }

  function parseNumber(text) {
    const t = text.trim().replace(",", ".");
    let m = t.match(/^([+-]?\d+)\s*\/\s*(\d+)$/);
    if (m) {
      if (BigInt(m[2]) === 0n) throw new Error("Enter a number such as 2.75, -0.375 or 3/8.");
      return fraction(BigInt(m[1]), BigInt(m[2]));
    }
    m = t.match(/^([+-]?)(\d*)(?:\.(\d*))?(?:[eE]([+-]?\d{1,3}))?$/);
    if (!m || (m[2] + (m[3] || "")) === "") throw new Error("Enter a number such as 2.75, -0.375 or 3/8.");
    const frac = m[3] || "";
    let n = BigInt((m[2] || "0") + frac), d = 10n ** BigInt(frac.length);
    const e = parseInt(m[4] || "0", 10);
    if (e > 0) n *= 10n ** BigInt(e); else d *= 10n ** BigInt(-e);
    if (m[1] === "-") n = -n;
    return fraction(n, d);
  }

  function encode(text) {
    const original = parseNumber(text);
    if (original.n === 0n) return { bits: "00000000", stored: fraction(0n, 1n), original, exact: true };

    const signBit = original.n < 0n ? "1" : "0";
    let n = original.n < 0n ? -original.n : original.n, d = original.d, exp = 0;
    while (n >= d && exp <= MAX_EXP) { d *= 2n; exp++; }
    while (2n * n < d && exp >= MIN_EXP) { n *= 2n; exp--; }

    if (exp > MAX_EXP) throw new Error("Overflow: the largest representable magnitude is 15/2 = 7.5.");
    if (exp < MIN_EXP) throw new Error("Underflow: the smallest representable magnitude is 1/32 = 0.03125.");

    const mant = (n * SCALE) / d;                       // truncates extra bits
    const bits = signBit + (exp + BIAS).toString(2).padStart(3, "0") + mant.toString(2).padStart(4, "0");
    const stored = decode(bits);
    const exact = (n * SCALE) % d === 0n;
    const lost = fraction(original.n * stored.d - stored.n * original.d, original.d * stored.d);
    return { bits, stored, original, exact, lost };
  }

  const api = { decode, encode, parseNumber, formatValue };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.Converter = api;
})(this);
