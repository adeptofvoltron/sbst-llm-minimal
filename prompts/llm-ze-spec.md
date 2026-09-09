---
model: claude-opus-5
effort: high
zabronione: "patches/, docs/, tests_sbst/, tests_hybryda/, raport/"
wyjscie: "tests_llm/test_loyalty.py, tests_llm/test_invoice.py"
---

Napisz testy jednostkowe weryfikujace, ze kod w `src/` realizuje uzgodniona
regule biznesowa.

Zrodlem prawdy o wymaganiach jest `SPEC.md`. Kod to `src/loyalty.py`
i `src/invoice.py`.

Najwazniejsza zasada: **oracle wyprowadzasz ze specyfikacji, nie z kodu.**
Jesli kod robi cos innego niz mowi `SPEC.md`, test ma sprawdzac zachowanie
**zgodne ze specyfikacja** - czyli ma nie przechodzic na obecnym kodzie.
Nie dopasowuj asercji do tego, co kod aktualnie zwraca.

Wymagania techniczne:

- pytest, pliki `tests_llm/test_loyalty.py` i `tests_llm/test_invoice.py`
- importuj moduly wprost (`import loyalty`, `import invoice`) - testy sa
  uruchamiane z `PYTHONPATH=src`
- kazda asercja o regule biznesowej ma w komentarzu lub w nazwie testu
  odwolanie do sekcji `SPEC.md`, z ktorej wynika
- nie zmieniaj niczego w `src/`

Ograniczenia:

- NIE czytaj i nie otwieraj katalogow `patches/`, `docs/`, `tests_sbst/`,
  `tests_hybryda/`, `raport/`. Zawieraja rozwiazanie zadania.

Na koniec wypisz liste rozbieznosci miedzy kodem a specyfikacja, ktore
znalazles: plik, regula ze specyfikacji, co robi kod.
