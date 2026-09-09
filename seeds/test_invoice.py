# Ziarna semantyczne dla Pynguina (--initial-population-seeding).
#
# To NIE jest suite testowy - to przypadki, ktore LLM napisalby po
# przeczytaniu SPEC.md, podane przeszukiwaniu jako populacja poczatkowa.
# Mechanizm z CodaMosy: model dostarcza wejscia, ktorych losowanie nie
# zgadnie, algorytm robi z nich reszte.
#
# Nazwa pliku ma znaczenie: Pynguin szuka w katalogu pliku, ktorego nazwa
# zawiera jednoczesnie nazwe modulu i "test_" (analyses/seeding.py).
import pytest
import invoice as module_0


def test_case_0():
    str_0 = "FV/2026/09/0042"
    dict_0 = module_0.parse_invoice_id(str_0)


def test_case_1():
    str_0 = "FV/1999/01/0001"
    with pytest.raises(ValueError):
        module_0.parse_invoice_id(str_0)


def test_case_2():
    str_0 = "FV/2026/09/0000"
    with pytest.raises(ValueError):
        module_0.parse_invoice_id(str_0)
