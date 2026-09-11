# Krok po kroku

Osiem komend. Najdluzsza trwa **3 sekundy**. Zero wywolan API - wszystkie
wyniki LLM-a sa zacommitowane.

Kolumna "co powiedziec" jest tylko podpowiedzia, nie scenariuszem.

---

## Zanim wejdziesz na scene

```bash
git clone https://github.com/adeptofvoltron/sbst-llm-minimal
cd sbst-llm-minimal
make setup
```

Sprawdz, ze dziala:

```bash
make sbst MODUL=loyalty && make fwpw
```

Powinienes zobaczyc `assert 172 == 171`. Jesli tak - jestes gotowy.
Na koniec `make czysto`.

---

## 1. Kod (30 s)

```bash
cat src/loyalty.py
```

```python
def award_points(order_value_pln: float, lifetime_spend_pln: float) -> int:
    if order_value_pln < 0 or lifetime_spend_pln < 0:
        raise ValueError("amounts must not be negative")

    points = int(order_value_pln // 10)

    if lifetime_spend_pln > VIP_THRESHOLD_PLN:
        points = points * 2

    if points > POINTS_CAP:
        return POINTS_CAP
    return points
```

**Co powiedziec:** osiem linii, zero magii, przechodzi review. A teraz
specyfikacja.

```bash
sed -n '/Przelicznik/,/parzystej/p' SPEC.md
```

> Klient otrzymuje **1 punkt za kazde 10 zlotych**. Wynik dzielenia
> zaokraglamy **metoda bankierska**.

**Co powiedziec:** `//` obcina w dol. To nie jest zaokraglenie bankierskie.
Druga rozbieznosc: specyfikacja mowi VIP to **co najmniej** 5000, kod ma `>`.
Zaden wyjatek nie leci, kod jest wewnetrznie spojny - po prostu liczy inaczej,
niz uzgodniono.

---

## 2. SBST generuje testy (3 s)

```bash
make sbst MODUL=loyalty
```

```bash
sed -n '5,12p' tests_sbst/test_loyalty.py
```

```python
def test_case_0():
    float_0 = 1716.363
    int_0 = module_0.award_points(float_0, float_0)
    assert int_0 == 171
```

**Co powiedziec:** `1716.363 / 10 = 171.6363`. Specyfikacja wymaga `172`.
Narzedzie uruchomilo funkcje, zobaczylo `171` i **to** zapisalo jako
oczekiwanie. Nie zna wymagan - zna tylko kod.

---

## 3. Puenta: naprawiamy kod, testy sie psuja (1 s)

```bash
make fwpw
```

```
=== przed patchem (kod z defektem) ===
3 passed in 0.01s

=== po patchu (kod zgodny ze SPEC.md) ===
FAILED tests_sbst/test_loyalty.py::test_case_0 - assert 172 == 171
FAILED tests_sbst/test_loyalty.py::test_case_2 - assert 438 == 437
2 failed, 1 passed in 0.02s

(patch cofniety)
```

**Co powiedziec:** `assert 172 == 171`. Naprawilem blad zgodnie ze
specyfikacja i dostalem czerwony build. Ten suite jest zapora regresji
chroniaca blad.

To nie awaria narzedzia - to jego zalozenie. I to jest jedyny sposob, zeby
to zobaczyc: nalozyc poprawke i sprawdzic, czy testy zmienily zdanie.
Nazywa sie **Fails Without / Passes With**.

> Poprawka to jedna linia: `round(order_value_pln / 10)`. W Pythonie `round()`
> **jest** zaokragleniem bankierskim - `round(2.5) == 2`, `round(3.5) == 4`.

---

## 4. Bramka formatu (3 s)

```bash
sed -n '5p' src/invoice.py
```

```python
_PATTERN = re.compile(r"^FV/(\d{4})/(0[1-9]|1[0-2])/(\d{4})$")
```

```bash
make sbst MODUL=invoice
cat tests_sbst/test_invoice.py
```

Cale wygenerowane testy:

```python
def test_case_0():
    str_0 = "!0s"
    with pytest.raises(ValueError):
        module_0.parse_invoice_id(str_0)
```

**Co powiedziec:** jeden test. Losowy string. Wyjatek. Cala logika za bramka -
zakres roku, zerowy numer, zwracany slownik - nietknieta. Poprawny prefiks to
pietnascie znakow w ustalonej kolejnosci; losowanie nie ma jak na to trafic.

---

## 5. Ziarna semantyczne - i pulapka (3 s)

```bash
cat seeds/test_invoice.py
```

**Co powiedziec:** trzy przypadki, ktore LLM napisalby po przeczytaniu
specyfikacji. Podajemy je przeszukiwaniu jako populacje poczatkowa. To
mechanizm CodaMosy, w Pynguinie dostepny jako flaga.

```bash
make ziarna MODUL=invoice
make raport MODUL=invoice
```

```
pokrycie RAPORTOWANE przez Pynguina (w trakcie przeszukiwania):
  sbst     "invoice","0.2222222222222222","0.2222222222222222"
  ziarna   "invoice","0.8888888888888888","0.8888888888888888","3"

pokrycie FAKTYCZNE wygenerowanych plikow (pytest-cov):
  === tests_sbst ===
  src/invoice.py      14      8      6      1    35%
  === tests_ziarna ===
  src/invoice.py      14      8      6      1    35%
  === tests_llm ===
  src/invoice.py      14      0      6      0   100%
```

**Co powiedziec:** gora ekranu - ziarna podniosly pokrycie z 22% na 89%,
cztery razy. Dol ekranu - **oba wygenerowane pliki maja 35%.** Ziarna pokryly
logike w trakcie przeszukiwania i nie trafily do eksportowanego suite.

Gdybym wzial liczbe z raportu na slajd, opowiadalbym bajke. Morał: **mierz
artefakt, nie raport narzedzia.**

> Sprawdzone przy budzecie 20 s i 60 s, przy podniesionym timeoucie,
> `--seed-from-archive` i `--initial-population-mutations 0`. Za kazdym razem
> 35%. Szczegoly: `docs/USTALENIA.md`, punkt 1.

---

## 6. LLM ze specyfikacja (1 min, bez API)

Ostatni wiersz poprzedniej tabeli: **100%**.

```bash
grep "^def test" tests_llm/test_loyalty.py | head -4
```

```python
def test_przelicznik_przyklady_ze_spec_sekcja_1(order_value_pln, oczekiwane):
def test_przelicznik_zaokraglenie_bankierskie_sekcja_1(order_value_pln, ...):
```

**Co powiedziec:** nazwy testow to zdania o wymaganiach, z numerem sekcji
specyfikacji. Porownaj z `test_case_0`.

Teraz ta sama walidacja, ktora zdemaskowala suite SBST - tylko na tym suite:

```bash
make fwpw KATALOG=tests_llm
```

```
=== przed patchem (kod z defektem) ===
16 failed, 28 passed in 0.10s

=== po patchu (kod zgodny ze SPEC.md) ===
44 passed in 0.04s
```

**Co powiedziec:** dokladnie odwrotnie niz przy SBST. Szesnascie testow nie
przechodzi na kodzie z defektami - **i to jest poprawny wynik**. Po nalozeniu
poprawki wszystkie 44 sa zielone.

To jest cala roznica miedzy tymi dwoma suite: nie w pokryciu, nie w liczbie
testow, a w tym, **skad wzielo sie oczekiwanie**.

A teraz drugi modul, i tu robi sie ciekawie:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests_llm/test_invoice.py -q
```

```
FAILED tests_llm/test_invoice.py::test_walidacja_cyfry_spoza_ascii_sekcja_2
1 failed, 49 passed
```

**Co powiedziec:** jeden test nie przechodzi i nie ma nic wspolnego
z zaokraglaniem. W kodzie byly **dwie** zasiane rozbieznosci. Ta jest trzecia.

---

## 7. Defekt, ktorego nikt nie zasial (1 min)

```bash
PYTHONPATH=src .venv/bin/python
```

```python
>>> import invoice
>>> invoice.parse_invoice_id("FV/٢٠٢٦/09/0042")
{'year': 2026, 'month': 9, 'seq': 42}
```

**Co powiedziec:** to ten test, ktory nie przechodzil. Rok zapisany cyframi
arabsko-indyjskimi przeszedl walidacje.

```python
>>> import re
>>> re.match(r"\d{4}", "٢٠٢٦")
<re.Match object; span=(0, 4), match='٢٠٢٦'>
>>> int("٢٠٢٦")
2026
```

**Co powiedziec:** `\d` w Pythonie domyslnie dopasowuje cyfry Unicode,
a `int()` je konwertuje. W kodzie byly **dwie** zasiane rozbieznosci - ta jest
trzecia i nie umiescil jej tam nikt. Znalazl ja LLM, ktory dostal wymagania.
Przeszukiwanie nie dotknelo jej ani razu.

Miesiac odrzuca takie wejscie, bo `(0[1-9]|1[0-2])` wymaga literalnych znakow
ASCII - wiec defekt dotyczy tylko roku i numeru kolejnego. Tym trudniej go
zauwazyc.

Poprawka to flaga: `re.compile(..., re.ASCII)`.

---

## 8. Domkniecie (30 s)

```bash
PYNGUIN_DANGER_AWARE=1 .venv/bin/pynguin --help \
  | grep -oE "\-\-call-llm-on-stall-detection|\-\-max-plateau-len|\-\-llm-url" | sort -u
```

```
--call-llm-on-stall-detection
--llm-url
--max-plateau-len
```

**Co powiedziec:** hybryda z artykulu - LLM wolany, gdy przeszukiwanie
staje - jest w Pynguinie **wbudowana jako flaga**. Nie trzeba jej budowac,
trzeba ja wlaczyc i dac endpoint zgodny z OpenAI.

Opakowane w `make hybryda`. Jedyny cel w tym repozytorium, ktory wymaga
klucza i wychodzi do sieci - dlatego nie ma go w scenariuszu prezentacji:

```bash
cp .env.op .env          # wstaw klucz; .env jest w .gitignore
make hybryda MODUL=invoice
```

Dwie pulapki po drodze (`docs/USTALENIA.md` punkt 8): bez `python-dotenv`
Pynguin ignoruje `.env` bez slowa, a `LLM_MODEL` ze srodowiska przegrywa
z niepusta wartoscia domyslna `gpt-4o-mini`.

---

## Porzadki

```bash
make czysto
git checkout -- src/
git status --short      # ma byc pusto
```

---

## Gdyby cos nie wyszlo

| Objaw | Przyczyna |
|---|---|
| `Environment variable 'PYNGUIN_DANGER_AWARE' not set` | uruchamiasz Pynguina bez `make`; ustaw `PYNGUIN_DANGER_AWARE=1` - dotyczy takze `--help`, ktory bez tej zmiennej wypisuje skrocona pomoc |
| `Provided testcases are not used.` | `--initial-population-data` musi wskazywac **katalog**, a plik w nim nazywac sie `test_<modul>.py` |
| inne liczby niz w tym dokumencie | zmienil sie `BUDZET` albo `ZIARNO`; przeszukiwanie jest stochastyczne |
| `make setup` nie dziala | brak `uv`; uzyj `python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'` |
