# Ustalenia

Co wyszlo w tym repozytorium, razem z tym, co wyszlo **inaczej niz zakladalismy**.

---

## 1. Pynguin raportuje pokrycie, ktorego wygenerowany plik nie ma

To najwazniejsze ustalenie i jedyny powod, dla ktorego warto przeczytac ten
dokument przed uzyciem liczb z `make ziarna` w prezentacji.

Ziarna semantyczne podniosly pokrycie **raportowane przez Pynguina**
z 22,2% do 88,9%, przy tym samym ziarnie losowym i tym samym budzecie:

```bash
make sbst   MODUL=invoice    # raport: 0.2222
make ziarna MODUL=invoice    # raport: 0.8889, FoundTestCases: 3
```

Wygenerowane pliki zmierzone niezaleznie, przez `pytest-cov`:

```bash
make pokrycie MODUL=invoice
```

```
=== tests_sbst ===
src/invoice.py      14      8      6      1    35%
=== tests_ziarna ===
src/invoice.py      14      8      6      1    35%
```

**Oba 35%.** Ani jeden wygenerowany test nie zawiera poprawnego numeru
faktury - `grep -c 'FV/' tests_ziarna/test_invoice.py` daje `0`.

Co sie dzieje: ziarna weszly do populacji poczatkowej i **w trakcie
przeszukiwania** faktycznie pokryly logike za bramka - stad 88,9% w raporcie.
Do **eksportowanego suite** nie trafily. Sprawdzone przy `--maximum-search-time`
20 i 60 s, przy `--maximum-test-execution-timeout 20`, przy
`--seed-from-archive True` i `--initial-population-mutations 0` - za kazdym
razem 35%.

Wniosek praktyczny: **mierz artefakt, nie raport narzedzia.** Dokladnie ta sama
pulapka wystapila w wersji TypeScriptowej z mutation testingiem, gdzie Stryker
przerywal przebieg, a harness odczytywal nieodswiezony raport i przypisywal
jednemu branchowi liczby innego.

## 2. Bramka formatu trzyma identycznie w obu jezykach

`parse_invoice_id` za wyrazeniem `^FV/(\d{4})/(0[1-9]|1[0-2])/(\d{4})$`:

| | wygenerowanych testow | pokrycie |
|---|---|---|
| SynTest (TypeScript, 90 s) | 13 | 60% galezi, 0 stringow od `FV` |
| Pynguin (Python, 20 s) | **1** | 35%, 0 stringow od `FV` |

Pynguin generuje jeden test i konczy, bo szybko wyczerpuje osiagalne cele.
SynTest generuje trzynascie i zaden nie jest lepszy. Rzecz nie w narzedziu,
tylko w rozkladzie: poprawny prefiks to 15 znakow w ustalonej kolejnosci,
a losowanie nie ma jak na to trafic.

## 3. Testy Pynguina sa czytelne. Testy SynTesta nie sa

Cale wyjscie Pynguina dla `invoice`, bez skrotow:

```python
def test_case_0():
    str_0 = "!0s"
    with pytest.raises(ValueError):
        module_0.parse_invoice_id(str_0)
```

Odpowiednik z SynTesta to 21 KB na trzynascie testow, z blokami metadanych
przeszukiwania i nieuzywanymi zmiennymi w kazdym tescie. Nazwy w obu
przypadkach sa bez wartosci (`test_case_0`, `Test N for '<modul>'`), ale
sam kod da sie u Pynguina przeczytac na glos.

## 4. `round()` w Pythonie to zaokraglenie bankierskie

Specyfikacja wymaga zaokraglenia bankierskiego, kod uzywa `//`. Poprawka to
`round(order_value_pln / 10)` - bo `round()` w Pythonie **domyslnie**
zaokragla polowki do liczby parzystej (`round(2.5) == 2`, `round(3.5) == 4`).

W TypeScripcie ten sam patch wymagal osobnej funkcji `roundHalfToEven`
(dziewiec linii). Roznica jezyka, nie metody - ale przy okazji dobry przyklad
tego, jak "oczywista" implementacja reguly zalezy od standardowej biblioteki.

## 5. Hybryda w Pynguinie to flagi, nie pipeline

Artykul opisuje CodaMose jako polaczenie Codeksa z Pynguinem. W Pynguinie 0.46
ten mechanizm jest **wbudowany**:

```
--call-llm-on-stall-detection     wywolaj LLM, gdy pokrycie staje
--max-plateau-len 25              po ilu iteracjach bez postepu
--call-llm-for-uncovered-targets  wywolaj dla niepokrytych celow
--hybrid-initial-population       testy od LLM w populacji poczatkowej
--llm-test-case-percentage        jaki ich udzial
--llm-url                         dowolny endpoint zgodny z OpenAI
```

Nie uzywamy ich w tym repozytorium, bo wymagaja klucza do API zgodnego
z OpenAI, a chcielismy, zeby wszystko dalo sie odtworzyc bez niego. Warto
jednak wiedziec, ze czterostopniowy pipeline z wersji TypeScriptowej
(intencja -> ziarna -> przeszukiwanie -> oracle) jest w Pythonie dostepny
jako kilka flag.

## 6. LLM ze specyfikacja znalazl defekt, ktorego nikt nie zasial

W kodzie byly **dwie** celowe rozbieznosci (zaokraglenie i prog VIP). Suite
wygenerowany przez LLM-a wykryl je obie - 17 z 94 testow nie przechodzi na
kodzie z defektami, a po nalozeniu `patches/fix_loyalty.patch` zostaje
**jeden** fail. I nie dotyczy zaokraglania:

```
FAILED tests_llm/test_invoice.py::test_walidacja_cyfry_spoza_ascii_sekcja_2
```

```python
def test_walidacja_cyfry_spoza_ascii_sekcja_2():
    with pytest.raises(ValueError, match="^malformed invoice id$"):
        invoice.parse_invoice_id("FV/٢٠٢٦/09/0042")
```

Sprawdzenie wprost:

```python
>>> invoice.parse_invoice_id("FV/٢٠٢٦/09/0042")
{'year': 2026, 'month': 9, 'seq': 42}

>>> re.match(r"\d{4}", "٢٠٢٦")
<re.Match object; span=(0, 4), match='٢٠٢٦'>

>>> int("٢٠٢٦")
2026
```

**`\d` w Pythonie domyslnie dopasowuje cyfry Unicode**, nie tylko ASCII,
a `int()` je konwertuje. Rok zapisany cyframi arabsko-indyjskimi przechodzil
walidacje. Miesiac nie przechodzi, bo `(0[1-9]|1[0-2])` wymaga literalnych
znakow ASCII - defekt dotyczy wiec tylko roku i numeru kolejnego, co czyni
go jeszcze trudniejszym do zauwazenia.

Poprawka to flaga: `re.compile(..., re.ASCII)` - patrz
`patches/fix_invoice_unicode.patch`.

Defekt zostaje w kodzie. To drugi taki przypadek w tej serii: w wersji
TypeScriptowej ten sam krok (LLM z dostepem do wymagan) znalazl, ze
`COUPONS["constructor"]` zwraca funkcje z `Object.prototype`, wiec walidacja
kuponu przepuszcza nazwy wlasnosci, a `total()` zwraca `NaN`. W obu jezykach
niezasiany defekt znalazlo to samo: **oracle wyprowadzony z wymagan, nie
z kodu.** Przeszukiwanie nie dotknelo zadnego z nich.

## 7. Pomoc CLI Pynguina wprowadza w blad w jednym miejscu

```
--initial-population-data str
    The path to the file with the pre-existing tests.
    The path has to include the file itself.
```

Podanie sciezki do pliku **nie dziala**. `analyses/seeding.py` robi
`os.walk(module_path)` i szuka pliku, ktorego nazwa zawiera *jednoczesnie*
nazwe modulu i `test_`:

```python
if module_name in name and "test_" in name:
```

Czyli: trzeba podac **katalog**, a plik w nim musi nazywac sie
`test_<modul>.py`. Przy sciezce do pliku w logu pojawia sie tylko
`Provided testcases are not used.` - bez wskazania przyczyny.
Stad `seeds/test_invoice.py`, a nie `seeds/ziarna.py`.
