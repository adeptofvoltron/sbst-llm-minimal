"""Identyfikator faktury. Regula biznesowa: SPEC.md, sekcja 2."""

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
