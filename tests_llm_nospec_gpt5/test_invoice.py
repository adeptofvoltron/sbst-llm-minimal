import pytest
import invoice


# Business rule (SPEC.md §2), as exercised by these tests:
# - Identifier format: "FV/YYYY/MM/NNN"
#   - Literal "FV" prefix
#   - Year: four digits, 2000–2099 inclusive
#   - Month: two digits, 01–12
#   - Sequence: three digits, 001–999 (exactly three digits, cannot be 000)
# - No surrounding whitespace is allowed.
# - The parser returns a dict with numeric fields: {"year": int, "month": int, "seq": int}


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("FV/2000/01/001", {"year": 2000, "month": 1, "seq": 1}),
        ("FV/2023/07/123", {"year": 2023, "month": 7, "seq": 123}),
        ("FV/2099/12/999", {"year": 2099, "month": 12, "seq": 999}),
    ],
)
def test_parses_valid_ids_with_three_digit_sequence(raw, expected):
    # Valid identifiers per SPEC.md §2 must be accepted and correctly parsed.
    assert invoice.parse_invoice_id(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "FV/1999/12/123",  # year too low
        "FV/2100/01/123",  # year too high (upper bound is 2099)
    ],
)
def test_rejects_year_out_of_range(raw):
    with pytest.raises(ValueError):
        invoice.parse_invoice_id(raw)


@pytest.mark.parametrize(
    "raw",
    [
        "FV/2023/00/123",  # month 00
        "FV/2023/13/123",  # month > 12
        "FV/2023/7/123",   # month not zero-padded to two digits
    ],
)
def test_rejects_invalid_months(raw):
    with pytest.raises(ValueError):
        invoice.parse_invoice_id(raw)


@pytest.mark.parametrize(
    "raw",
    [
        "FV/2023/07/000",  # sequence cannot be 000
    ],
)
def test_rejects_sequence_zero(raw):
    with pytest.raises(ValueError):
        invoice.parse_invoice_id(raw)


@pytest.mark.parametrize(
    "raw",
    [
        "FV/2023/07/1000",  # sequence must be exactly three digits
        "FV/2023/07/0123",  # four digits, and leading zero not allowed because width must be 3
    ],
)
def test_rejects_four_digit_sequences(raw):
    with pytest.raises(ValueError):
        invoice.parse_invoice_id(raw)


@pytest.mark.parametrize(
    "raw",
    [
        " fv/2023/07/123",   # lowercase prefix not allowed and leading space
        "FV/2023/07/123 ",   # trailing space not allowed
        " FV/2023/07/123 ",  # surrounding whitespace not allowed
    ],
)
def test_rejects_whitespace_and_prefix_variants(raw):
    with pytest.raises(ValueError):
        invoice.parse_invoice_id(raw)
