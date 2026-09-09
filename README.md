# SBST vs LLM vs hybryda - minimalny przyklad

Ten sam eksperyment co w
[ai-kielce-prezentacja](https://github.com/adeptofvoltron/ai-kielce-prezentacja),
ale sprowadzony do **czterdziestu linii kodu produkcyjnego** i narzedzia,
ktore nie wymaga zadnego etapu budowania.

Dlaczego Python: **narzedzia SBST natywnego dla TypeScriptu nie ma.** Sprawdzone
na npm - jedyne trafienie na "sbst" to klient REST do EvoMastera, `jsfuzz`
porzucony w 2022. Dla JS/TS zostaje SynTest, ktory nie parsuje TypeScriptu,
wiec wymaga `tsc`, mapowania modulow i transformacji wyniku (siedem obejsc,
opisanych w tamtym repozytorium).

**Pynguin** dla Pythona nie wymaga niczego z tej listy. Zadnego builda,
zadnej konfiguracji. To dodatkowo dokladnie ten tool, na ktorym zbudowano
**CodaMose** - hybryde cytowana w artykule.

```
przeszukiwanie jednego modulu:  3 sekundy
caly setup:                     dwie komendy
kod produkcyjny:                40 linii
```

## Wynik w jednej tabeli

`make pokrycie MODUL=invoice` - faktyczne pokrycie wygenerowanych plikow,
mierzone `pytest-cov`, nie raportowane przez narzedzie:

| | testow | pokrycie `invoice.py` | rozbieznosc ze SPEC |
|---|---|---|---|
| SBST (Pynguin, 20 s) | 1 | **35%** | utrwalona |
| SBST + ziarna semantyczne | 4 | **35%** | utrwalona |
| LLM ze specyfikacja | 50 | **100%** | **wykryta** |

Trzy rzeczy, ktore z tego wynikaja i ktorych nie planowalismy:

1. **Ziarna podniosly pokrycie raportowane przez Pynguina z 22,2% na 88,9%,
   a pokrycie wygenerowanego pliku ani o punkt.** Mierz artefakt, nie raport.
2. **LLM ze specyfikacja znalazl defekt, ktorego nikt nie zasial**: `\d`
   w Pythonie dopasowuje cyfry Unicode, wiec `FV/٢٠٢٦/09/0042` przechodzilo
   walidacje, a `int()` grzecznie zwracalo `2026`.
3. **Hybryda z artykulu jest w Pynguinie flaga**, nie pipeline'em -
   `--call-llm-on-stall-detection`, `--max-plateau-len`, `--llm-url`.

Szczegoly kazdej z nich: [`docs/USTALENIA.md`](docs/USTALENIA.md).

---

## Chcesz to pokazac?

[`KROK-PO-KROKU.md`](KROK-PO-KROKU.md) - osiem komend, najdluzsza 3 sekundy,
zero wywolan API. Kazda komenda i kazdy oczekiwany wynik zostaly wykonane
dokladnie tak, jak sa zapisane.

---

## Setup

```bash
git clone https://github.com/adeptofvoltron/sbst-llm-minimal
cd sbst-llm-minimal
make setup
```

`make setup` robi `uv venv --python 3.12` i `uv pip install -e '.[dev]'`.
Bez `uv`:

```bash
python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'
```

Wymagany Python 3.10-3.14 (Pynguin 0.46 nie wspiera 3.15+).

---

## Kod, ktory dziala i realizuje zla regule

`src/loyalty.py`, caly:

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

`SPEC.md` sekcja 1 mowi dwie rzeczy inaczej:

- punkty zaokraglamy **metoda bankierska** - a `//` obcina w dol,
- VIP to suma zakupow **co najmniej** 5000 zl - a w kodzie jest `>`.

Smaczek dla Pythona: `round()` **jest** zaokragleniem bankierskim
(`round(2.5) == 2`, `round(3.5) == 4`). Poprawka to jedna linia -
patrz `patches/fix_loyalty.patch`.

---

## Krok 1: SBST generuje testy z zachowania kodu (3 s)

```bash
make sbst MODUL=loyalty
```

```python
def test_case_0():
    float_0 = 1716.363
    int_0 = module_0.award_points(float_0, float_0)
    assert int_0 == 171
```

`1716.363 / 10 = 171.6363`. Specyfikacja wymaga `172`. Kod zwraca `171`,
bo obcina w dol - i test wlasnie to przypial jako oczekiwanie.

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests_sbst/test_loyalty.py -q
```

```
3 passed
```

Zielono - i nie moglo byc inaczej.

---

## Krok 2: naprawiamy kod, testy sie psuja (1 s)

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

**`assert 172 == 171`** - jedna linia, ktora mowi wszystko. Naprawa zgodna
ze specyfikacja lamie testy. Suite dziala jako zapora regresji chroniaca blad.

To nie awaria narzedzia. To jego zalozenie: kod jest zrodlem prawdy o tym,
co ma sie dziac. Nazywa sie to **walidacja tautologiczna**
(Fails Without / Passes With) i jest jedynym sposobem odroznienia
"test wykryl blad" od "test utrwalil blad".

---

## Krok 3: bramka formatu (3 s)

`src/invoice.py` ma jedna linie, ktora decyduje o wszystkim:

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

**Jeden test. Losowy string. Wyjatek.** Cala logika za bramka - zakres roku,
zerowy numer kolejny, zwracany slownik - jest nietkniete.

```bash
make pokrycie MODUL=invoice
```

```
=== tests_sbst ===
src/invoice.py      14      8      6      1    35%
```

---

## Krok 4: ziarna semantyczne (3 s)

`seeds/test_invoice.py` to trzy przypadki, ktore LLM napisalby po przeczytaniu
`SPEC.md` - podane przeszukiwaniu jako **populacja poczatkowa**. Mechanizm
z CodaMosy, w Pynguinie dostepny jako flaga:

```bash
make ziarna MODUL=invoice
```

Pynguin raportuje:

| | pokrycie galezi (raport Pynguina) |
|---|---|
| bez ziaren | **22,2%** |
| z ziarnami | **88,9%** (`FoundTestCases: 3`) |

Cztery razy wiecej, przy tym samym ziarnie losowym i tym samym budzecie.

**Ale to nie jest cala prawda** - i to jest najciekawsza rzecz w tym
repozytorium. Patrz [`docs/USTALENIA.md`](docs/USTALENIA.md), punkt 1.

---

## Krok 5: LLM ze specyfikacja

Testy sa zacommitowane, wiec ten krok nie wymaga klucza API. Prompt jest
w [`prompts/llm-ze-spec.md`](prompts/llm-ze-spec.md) razem z uzytym modelem
i poziomem effortu, transkrypt z kazdym wywolaniem narzedzia w `artifacts/`.

```bash
make pokrycie MODUL=loyalty
make fwpw KATALOG=tests_llm
```

Zeby wygenerowac od nowa (wymaga Claude Code):

```bash
bash run-llm.sh prompts/llm-ze-spec.md
```

---

## Wszystkie komendy

| Komenda | Co robi | Czas |
|---|---|---|
| `make setup` | srodowisko | ~20 s |
| `make sbst MODUL=loyalty` | przeszukiwanie | 3 s |
| `make ziarna MODUL=invoice` | przeszukiwanie z ziarnami | 3 s |
| `make pokrycie MODUL=invoice` | faktyczne pokrycie wygenerowanych plikow | 1 s |
| `make raport MODUL=invoice` | raport Pynguina **obok** faktycznego pokrycia | 2 s |
| `make fwpw` | walidacja Fails Without / Passes With | 1 s |
| `make czysto` | porzadki | - |

Zmienne: `MODUL` (`loyalty` \| `invoice`), `BUDZET` (sekundy),
`ZIARNO` (seed), `KATALOG` (`tests_sbst` \| `tests_llm` \| `tests_ziarna`).

---

## Co dalej

- [`docs/USTALENIA.md`](docs/USTALENIA.md) - co wyszlo, w tym pulapka
  pomiarowa Pynguina i **defekt, ktorego nikt nie zasial**: `\d` w Pythonie
  dopasowuje cyfry Unicode, wiec `FV/٢٠٢٦/09/0042` przechodzilo walidacje
- [`SPEC.md`](SPEC.md) - wymagania, czyli oracle
- pelna wersja eksperymentu z mutation testing, piecioma wariantami LLM
  i hybryda czterostopniowa:
  [ai-kielce-prezentacja](https://github.com/adeptofvoltron/ai-kielce-prezentacja)
