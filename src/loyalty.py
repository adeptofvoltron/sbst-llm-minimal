"""Punkty lojalnosciowe. Regula biznesowa: SPEC.md, sekcja 1."""

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
