# Specyfikacja biznesowa

> Ten plik gra role strony w Confluence: opisuje **intencje**, nie aktualne
> zachowanie kodu. W razie rozbieznosci obowiazuje ten dokument.

## Sekcja 1: Punkty lojalnosciowe

`award_points(order_value_pln, lifetime_spend_pln) -> int`

**Przelicznik.** Klient otrzymuje **1 punkt za kazde 10 zlotych** wartosci
zamowienia. Wynik dzielenia zaokraglamy **metoda bankierska**: do najblizszej
liczby calkowitej, a przy dokladnej polowie do liczby parzystej.

> Przyklady: `2,5 -> 2`, `3,5 -> 4`, `2,4 -> 2`, `2,6 -> 3`.

**Mnoznik VIP.** Klient, ktorego suma dotychczasowych zakupow wynosi
**co najmniej 5000 zlotych**, otrzymuje podwojona liczbe punktow.

**Limit.** Maksymalnie **5000 punktow** za jedno zamowienie, stosowany
po naliczeniu mnoznika VIP.

**Walidacja.** Ktorakolwiek kwota ujemna -> `ValueError("amounts must not be
negative")`.

## Sekcja 2: Identyfikator faktury

`parse_invoice_id(raw) -> dict`

**Format.** `FV/RRRR/MM/NNNN`, gdzie `RRRR` to rok (cztery cyfry), `MM` to
miesiac (`01`-`12`), `NNNN` to numer kolejny (cztery cyfry).
Przyklad poprawnej wartosci: `FV/2026/09/0042`.
Biale znaki na brzegach sa ignorowane.

**Walidacja**

| Warunek | Reakcja |
|---|---|
| nie pasuje do formatu | `ValueError("malformed invoice id")` |
| rok poza zakresem 2000-2100 | `ValueError("year out of supported range")` |
| numer kolejny rowny `0000` | `ValueError("sequence number must not be zero")` |

**Wynik.** `{"year": int, "month": int, "seq": int}` - bez wiodacych zer.
