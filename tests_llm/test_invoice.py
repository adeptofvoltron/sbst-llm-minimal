"""Testy jednostkowe dla `invoice.parse_invoice_id`.

Oracle pochodzi WYLACZNIE ze `SPEC.md`, sekcja 2 ("Identyfikator faktury").
Zadna asercja nie zostala dopasowana do aktualnego zachowania `src/invoice.py`.
"""

import pytest

import invoice


# ---------------------------------------------------------------------------
# SPEC.md sekcja 2 / "Format" + "Wynik"
# ---------------------------------------------------------------------------


def test_format_przyklad_ze_spec_sekcja_2():
    # SPEC.md sekcja 2 / "Format": "Przyklad poprawnej wartosci: FV/2026/09/0042".
    # SPEC.md sekcja 2 / "Wynik": {"year": int, "month": int, "seq": int}.
    assert invoice.parse_invoice_id("FV/2026/09/0042") == {
        "year": 2026,
        "month": 9,
        "seq": 42,
    }


def test_wynik_bez_wiodacych_zer_sekcja_2():
    # SPEC.md sekcja 2 / "Wynik": wartosci liczbowe "bez wiodacych zer".
    wynik = invoice.parse_invoice_id("FV/2000/01/0001")
    assert wynik == {"year": 2000, "month": 1, "seq": 1}
    assert all(isinstance(v, int) for v in wynik.values())


def test_wynik_ma_dokladnie_trzy_klucze_sekcja_2():
    # SPEC.md sekcja 2 / "Wynik": slownik z kluczami year, month, seq.
    assert set(invoice.parse_invoice_id("FV/2026/12/9999")) == {"year", "month", "seq"}


@pytest.mark.parametrize("miesiac, oczekiwany", [(f"{m:02d}", m) for m in range(1, 13)])
def test_format_akceptuje_miesiace_01_12_sekcja_2(miesiac, oczekiwany):
    # SPEC.md sekcja 2 / "Format": MM to miesiac w zakresie 01-12.
    assert invoice.parse_invoice_id(f"FV/2026/{miesiac}/0042")["month"] == oczekiwany


@pytest.mark.parametrize("surowy", [
    "  FV/2026/09/0042",
    "FV/2026/09/0042  ",
    "\tFV/2026/09/0042\n",
    "\n  FV/2026/09/0042 \t ",
])
def test_format_ignoruje_biale_znaki_na_brzegach_sekcja_2(surowy):
    # SPEC.md sekcja 2 / "Format": "Biale znaki na brzegach sa ignorowane."
    assert invoice.parse_invoice_id(surowy) == {"year": 2026, "month": 9, "seq": 42}


# ---------------------------------------------------------------------------
# SPEC.md sekcja 2 / "Walidacja": nie pasuje do formatu -> "malformed invoice id"
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("surowy", [
    "",
    "FV/2026/09/0042/",
    "FV/2026/09",
    "FV/2026/09/042",  # NNNN musi miec cztery cyfry
    "FV/2026/09/00042",  # pieciocyfrowy numer kolejny
    "FV/026/09/0042",  # RRRR musi miec cztery cyfry
    "FV/20260/09/0042",
    "FV/2026/9/0042",  # MM musi miec dwie cyfry
    "FV/2026/00/0042",  # miesiac 00 poza 01-12
    "FV/2026/13/0042",  # miesiac 13 poza 01-12
    "FV/2026/99/0042",
    "fv/2026/09/0042",  # prefiks jest wielkimi literami
    "FA/2026/09/0042",  # inny prefiks
    "2026/09/0042",  # brak prefiksu
    "FV-2026-09-0042",  # zly separator
    "FV/2026/09/004X",  # znak niebedacy cyfra
    "FV/ 2026/09/0042",  # biale znaki w srodku nie sa ignorowane
    "FV/2026/09/0042 FV/2026/09/0043",
    "przedrostek FV/2026/09/0042",
])
def test_walidacja_niepoprawny_format_sekcja_2(surowy):
    # SPEC.md sekcja 2 / "Walidacja": nie pasuje do formatu ->
    # ValueError("malformed invoice id").
    with pytest.raises(ValueError, match="^malformed invoice id$"):
        invoice.parse_invoice_id(surowy)


def test_walidacja_cyfry_spoza_ascii_sekcja_2():
    # SPEC.md sekcja 2 / "Format": identyfikator ma postac FV/RRRR/MM/NNNN
    # zapisana cyframi (przyklad: FV/2026/09/0042). Ciag zapisany cyframi
    # spoza ASCII nie jest ta postacia -> "malformed invoice id".
    with pytest.raises(ValueError, match="^malformed invoice id$"):
        invoice.parse_invoice_id("FV/٢٠٢٦/09/0042")


# ---------------------------------------------------------------------------
# SPEC.md sekcja 2 / "Walidacja": rok poza 2000-2100
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rok", ["1999", "1900", "0000", "2101", "9999"])
def test_walidacja_rok_poza_zakresem_sekcja_2(rok):
    # SPEC.md sekcja 2 / "Walidacja": rok poza zakresem 2000-2100 ->
    # ValueError("year out of supported range").
    with pytest.raises(ValueError, match="^year out of supported range$"):
        invoice.parse_invoice_id(f"FV/{rok}/09/0042")


@pytest.mark.parametrize("rok, oczekiwany", [("2000", 2000), ("2100", 2100)])
def test_walidacja_krance_zakresu_lat_sa_poprawne_sekcja_2(rok, oczekiwany):
    # SPEC.md sekcja 2 / "Walidacja": zakres 2000-2100 jest domkniety,
    # wiec oba krance sa akceptowane.
    assert invoice.parse_invoice_id(f"FV/{rok}/09/0042")["year"] == oczekiwany


# ---------------------------------------------------------------------------
# SPEC.md sekcja 2 / "Walidacja": numer kolejny 0000
# ---------------------------------------------------------------------------


def test_walidacja_numer_kolejny_zero_sekcja_2():
    # SPEC.md sekcja 2 / "Walidacja": numer kolejny rowny 0000 ->
    # ValueError("sequence number must not be zero").
    with pytest.raises(ValueError, match="^sequence number must not be zero$"):
        invoice.parse_invoice_id("FV/2026/09/0000")


def test_walidacja_numer_kolejny_0001_jest_poprawny_sekcja_2():
    # SPEC.md sekcja 2 / "Walidacja": tylko 0000 jest odrzucane.
    assert invoice.parse_invoice_id("FV/2026/09/0001")["seq"] == 1


def test_walidacja_najwyzszy_numer_kolejny_sekcja_2():
    # SPEC.md sekcja 2 / "Format": NNNN to cztery cyfry, wiec 9999 miesci sie
    # w formacie.
    assert invoice.parse_invoice_id("FV/2026/09/9999")["seq"] == 9999


def test_priorytet_bledu_formatu_nad_rokiem_sekcja_2():
    # SPEC.md sekcja 2 / "Walidacja": tabela sprawdzen zaczyna sie od formatu,
    # wiec ciag ktory nie pasuje do wzorca dostaje "malformed invoice id"
    # nawet jesli rok jest tez poza zakresem.
    with pytest.raises(ValueError, match="^malformed invoice id$"):
        invoice.parse_invoice_id("FV/1999/13/0000")
