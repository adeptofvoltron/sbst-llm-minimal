# Semantic seeds for Pynguin (--initial-population-seeding).
#
# This is NOT a test suite - these are the cases an LLM would write after
# reading SPEC.md, handed to the search as its initial population. The
# mechanism comes from CodaMosa: the model supplies inputs that random
# sampling will never guess, the algorithm does the rest.
#
# The file name matters: Pynguin looks in the directory for a file whose name
# contains both the module name and "test_" (analyses/seeding.py).
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
