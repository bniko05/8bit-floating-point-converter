"""Check that docs/converter.js (web version) agrees with converter.py."""
import json
import random
import shutil
import subprocess
from pathlib import Path

import pytest

from converter import ConversionError, decode, encode, format_value

JS_FILE = Path(__file__).resolve().parent.parent / "docs" / "converter.js"

NODE_SCRIPT = """
const C = require(process.argv[1]);
const inputs = JSON.parse(require("fs").readFileSync(0, "utf8"));
const out = { decode: [], encode: [] };
for (let i = 0; i < 256; i++) out.decode.push(C.formatValue(C.decode(i.toString(2).padStart(8, "0"))));
for (const x of inputs) {
  try { const r = C.encode(x); out.encode.push([r.bits, r.exact]); }
  catch (e) { out.encode.push(["error", e.message.split(":")[0]]); }
}
console.log(JSON.stringify(out));
"""


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js not installed")
def test_javascript_matches_python():
    rng = random.Random(0)
    inputs = ["0", "1", "2.625", "-0.375", "3/8", "7.99", "8", "0.03125", "1/64", "abc", "1e-2"]
    inputs += [f"{rng.uniform(-9, 9):.{rng.randint(0, 6)}f}" for _ in range(500)]
    inputs += [f"{rng.randint(-300, 300)}/{rng.randint(1, 97)}" for _ in range(200)]

    result = subprocess.run(
        ["node", "-e", NODE_SCRIPT, str(JS_FILE)],
        input=json.dumps(inputs), capture_output=True, text=True, check=True,
    )
    js = json.loads(result.stdout)

    assert js["decode"] == [format_value(decode(format(i, "08b"))) for i in range(256)]

    for text, js_result in zip(inputs, js["encode"]):
        try:
            enc = encode(text)
            expected = [enc.bits, enc.exact]
        except ConversionError as exc:
            expected = ["error", str(exc).split(":")[0]]
        assert js_result == expected, text
