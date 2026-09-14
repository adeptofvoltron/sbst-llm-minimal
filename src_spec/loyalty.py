"""Loyalty points.

BUSINESS SPECIFICATION - this is the source of truth. Where the code below
diverges from this text, the text wins and the code is wrong.

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
"""

VIP_THRESHOLD_PLN = 5000
POINTS_CAP = 5000


def award_points(order_value_pln: float, lifetime_spend_pln: float) -> int:
    if order_value_pln < 0 or lifetime_spend_pln < 0:
        raise ValueError("amounts must not be negative")

    points = int(order_value_pln // 10)

    if lifetime_spend_pln > VIP_THRESHOLD_PLN:
        points = points * 2

    if points > POINTS_CAP:
        return POINTS_CAP
    return points
