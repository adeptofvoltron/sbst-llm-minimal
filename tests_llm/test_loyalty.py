"""Testy jednostkowe dla `loyalty.award_points`.

Oracle pochodzi WYLACZNIE ze `SPEC.md`, sekcja 1 ("Punkty lojalnosciowe").
Zadna asercja nie zostala dopasowana do aktualnego zachowania `src/loyalty.py`.
Testy, ktore nie przechodza, wskazuja rozbieznosc kodu ze specyfikacja.
"""

from decimal import Decimal, ROUND_HALF_EVEN

import pytest

import loyalty


def oczekiwane_punkty_bazowe(order_value_pln) -> int:
    """Niezalezny oracle przelicznika ze SPEC.md, sekcja 1 / "Przelicznik".

    "1 punkt za kazde 10 zlotych (...) zaokraglamy metoda bankierska: do
    najblizszej liczby calkowitej, a przy dokladnej polowie do liczby parzystej."
    """
    iloraz = Decimal(str(order_value_pln)) / Decimal(10)
    return int(iloraz.quantize(Decimal(1), rounding=ROUND_HALF_EVEN))


# ---------------------------------------------------------------------------
# SPEC.md sekcja 1 / "Przelicznik"
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "order_value_pln, oczekiwane",
    [
        # Przyklady wprost ze SPEC.md sekcja 1 / "Przelicznik":
        # "2,5 -> 2, 3,5 -> 4, 2,4 -> 2, 2,6 -> 3" (ilorazy order_value/10).
        (25, 2),  # 2,5 -> polowa -> do parzystej -> 2
        (35, 4),  # 3,5 -> polowa -> do parzystej -> 4
        (24, 2),  # 2,4 -> w dol
        (26, 3),  # 2,6 -> w gore
    ],
)
def test_przelicznik_przyklady_ze_spec_sekcja_1(order_value_pln, oczekiwane):
    # SPEC.md sekcja 1 / "Przelicznik": zaokraglenie bankierskie ilorazu /10.
    assert loyalty.award_points(order_value_pln, 0) == oczekiwane


@pytest.mark.parametrize(
    "order_value_pln, oczekiwane",
    [
        (0, 0),
        (4, 0),  # 0,4 -> 0
        (5, 0),  # 0,5 -> polowa -> do parzystej -> 0
        (6, 1),  # 0,6 -> 1
        (10, 1),  # 1,0 -> 1
        (15, 2),  # 1,5 -> polowa -> do parzystej -> 2
        (45, 4),  # 4,5 -> polowa -> do parzystej -> 4
        (55, 6),  # 5,5 -> polowa -> do parzystej -> 6
        (99, 10),  # 9,9 -> 10
        (101, 10),  # 10,1 -> 10
        (1234, 123),  # 123,4 -> 123
        (1235, 124),  # 123,5 -> polowa -> do parzystej -> 124
        (1245, 124),  # 124,5 -> polowa -> do parzystej -> 124
    ],
)
def test_przelicznik_zaokraglenie_bankierskie_sekcja_1(order_value_pln, oczekiwane):
    # SPEC.md sekcja 1 / "Przelicznik": do najblizszej calkowitej,
    # przy dokladnej polowie do liczby parzystej (NIE obcinanie w dol).
    assert loyalty.award_points(order_value_pln, 0) == oczekiwane


@pytest.mark.parametrize("order_value_pln", [0, 3, 7, 12, 18, 25, 26, 35, 44, 250, 999])
def test_przelicznik_zgodny_z_niezaleznym_oraclem_sekcja_1(order_value_pln):
    # SPEC.md sekcja 1 / "Przelicznik": porownanie z oraclem zbudowanym
    # bezposrednio z tekstu specyfikacji (Decimal + ROUND_HALF_EVEN).
    assert loyalty.award_points(order_value_pln, 0) == oczekiwane_punkty_bazowe(
        order_value_pln
    )


def test_przelicznik_kwoty_ulamkowe_sekcja_1():
    # SPEC.md sekcja 1 / "Przelicznik": wartosc zamowienia nie musi byc
    # wielokrotnoscia 10 zl; liczy sie iloraz i jego zaokraglenie.
    assert loyalty.award_points(12.5, 0) == 1  # 1,25 -> 1
    assert loyalty.award_points(17.5, 0) == 2  # 1,75 -> 2
    assert loyalty.award_points(29.9, 0) == 3  # 2,99 -> 3


# ---------------------------------------------------------------------------
# SPEC.md sekcja 1 / "Mnoznik VIP"
# ---------------------------------------------------------------------------


def test_vip_dokladnie_na_progu_5000_dostaje_mnoznik_sekcja_1():
    # SPEC.md sekcja 1 / "Mnoznik VIP": "suma dotychczasowych zakupow wynosi
    # CO NAJMNIEJ 5000 zlotych" -> prog wlaczajacy (>=), nie ostry (>).
    assert loyalty.award_points(100, 5000) == 20  # 10 punktow x2


def test_vip_powyzej_progu_dostaje_mnoznik_sekcja_1():
    # SPEC.md sekcja 1 / "Mnoznik VIP": powyzej progu punkty sa podwojone.
    assert loyalty.award_points(100, 5000.01) == 20
    assert loyalty.award_points(100, 12345) == 20


def test_brak_vip_ponizej_progu_sekcja_1():
    # SPEC.md sekcja 1 / "Mnoznik VIP": ponizej 5000 zl brak podwojenia.
    assert loyalty.award_points(100, 0) == 10
    assert loyalty.award_points(100, 4999.99) == 10


def test_vip_mnozy_wynik_po_zaokragleniu_sekcja_1():
    # SPEC.md sekcja 1: mnoznik VIP dziala na "liczbe punktow", czyli na
    # wyniku przelicznika (juz zaokraglonym metoda bankierska), nie na kwocie.
    # 35 zl -> 3,5 -> 4 punkty -> VIP -> 8.
    assert loyalty.award_points(35, 9000) == 8


# ---------------------------------------------------------------------------
# SPEC.md sekcja 1 / "Limit"
# ---------------------------------------------------------------------------


def test_limit_5000_punktow_bez_vip_sekcja_1():
    # SPEC.md sekcja 1 / "Limit": maksymalnie 5000 punktow za jedno zamowienie.
    assert loyalty.award_points(100_000, 0) == 5000


def test_limit_nie_obniza_wyniku_ponizej_progu_sekcja_1():
    # SPEC.md sekcja 1 / "Limit": limit to gorne ograniczenie, dokladnie
    # 5000 punktow jest wartoscia dopuszczalna.
    assert loyalty.award_points(50_000, 0) == 5000
    assert loyalty.award_points(49_990, 0) == 4999


def test_limit_stosowany_po_mnozniku_vip_sekcja_1():
    # SPEC.md sekcja 1 / "Limit": "stosowany PO naliczeniu mnoznika VIP".
    # 60000 zl -> 6000 pkt -> VIP -> 12000 -> limit -> 5000
    # (gdyby limit dzialal przed mnoznikiem, wynik bylby 10000).
    assert loyalty.award_points(60_000, 9000) == 5000


def test_limit_vip_tuz_pod_limitem_sekcja_1():
    # SPEC.md sekcja 1 / "Limit" + "Mnoznik VIP": 24990 zl -> 2499 pkt
    # -> VIP -> 4998, czyli ponizej limitu -> zwracamy 4998.
    assert loyalty.award_points(24_990, 5000) == 4998


# ---------------------------------------------------------------------------
# SPEC.md sekcja 1 / "Walidacja"
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "order_value_pln, lifetime_spend_pln",
    [
        (-1, 0),
        (0, -1),
        (-1, -1),
        (-0.01, 10_000),
        (100, -0.01),
    ],
)
def test_walidacja_kwot_ujemnych_sekcja_1(order_value_pln, lifetime_spend_pln):
    # SPEC.md sekcja 1 / "Walidacja": ktorakolwiek kwota ujemna ->
    # ValueError("amounts must not be negative").
    with pytest.raises(ValueError, match="^amounts must not be negative$"):
        loyalty.award_points(order_value_pln, lifetime_spend_pln)


def test_zera_sa_poprawne_sekcja_1():
    # SPEC.md sekcja 1 / "Walidacja": ujemne sa niedozwolone, zero jest
    # poprawna kwota i daje 0 punktow.
    assert loyalty.award_points(0, 0) == 0


def test_zwraca_typ_int_sekcja_1():
    # SPEC.md sekcja 1: sygnatura `award_points(...) -> int`.
    assert isinstance(loyalty.award_points(26, 0), int)
    assert isinstance(loyalty.award_points(100_000, 9000), int)
