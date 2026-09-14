"""Invoice identifier.

BUSINESS SPECIFICATION - this is the source of truth. Where the code below
diverges from this text, the text wins and the code is wrong.

`parse_invoice_id(raw) -> dict`

**Format.** `FV/YYYY/MM/NNNN`, where `YYYY` is the year (four digits), `MM` is
the month (`01`-`12`) and `NNNN` is the sequence number (four digits).
Example of a valid value: `FV/2026/09/0042`.
Surrounding whitespace is ignored.

**Validation**

| Condition | Reaction |
|---|---|
| does not match the format | `ValueError("malformed invoice id")` |
| year outside the range 2000-2100 | `ValueError("year out of supported range")` |
| sequence number equal to `0000` | `ValueError("sequence number must not be zero")` |

**Result.** `{"year": int, "month": int, "seq": int}` - without leading zeros.
"""

import re

_PATTERN = re.compile(r"^FV/(\d{4})/(0[1-9]|1[0-2])/(\d{4})$")


def parse_invoice_id(raw: str) -> dict:
    match = _PATTERN.match(raw.strip())
    if match is None:
        raise ValueError("malformed invoice id")

    year = int(match.group(1))
    month = int(match.group(2))
    seq = int(match.group(3))

    if year < 2000 or year > 2100:
        raise ValueError("year out of supported range")
    if seq == 0:
        raise ValueError("sequence number must not be zero")

    return {"year": year, "month": month, "seq": seq}
