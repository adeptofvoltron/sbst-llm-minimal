# Business specification

> This file plays the part of a Confluence page: it describes **intent**, not
> the current behaviour of the code. Where the two differ, this document wins.

## Section 1: Loyalty points

`award_points(order_value_pln, lifetime_spend_pln) -> int`

**Conversion rate.** A customer earns **1 point for every 10 PLN** of order
value. The result of the division is rounded using **banker's rounding**: to
the nearest integer, and on an exact half to the even one.

> Examples: `2.5 -> 2`, `3.5 -> 4`, `2.4 -> 2`, `2.6 -> 3`.

**VIP multiplier.** A customer whose lifetime spend is **at least 5000 PLN**
earns double the points.

**Cap.** At most **5000 points** per order, applied after the VIP multiplier.

**Validation.** Either amount being negative -> `ValueError("amounts must not
be negative")`.

## Section 2: Invoice identifier

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
