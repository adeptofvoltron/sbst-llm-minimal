import pytest
import invoice


# SPEC.md Section 2: Invoice identifier - Result shape and whitespace handling
def test_parse_invoice_id_happy_path_ignores_surrounding_whitespace_and_returns_ints_spec_section_2():
    result = invoice.parse_invoice_id("  \tFV/2026/09/0042\n")
    assert result == {"year": 2026, "month": 9, "seq": 42}  # SPEC.md §2: returns ints without leading zeros


# SPEC.md Section 2: Invoice identifier - Year boundaries 2000-2100 inclusive
@pytest.mark.parametrize(
    "raw, expected",
    [
        ("FV/2000/01/0001", {"year": 2000, "month": 1, "seq": 1}),
        ("FV/2100/12/9999", {"year": 2100, "month": 12, "seq": 9999}),
    ],
)
def test_parse_invoice_id_accepts_boundary_years_2000_and_2100_spec_section_2(raw, expected):
    assert invoice.parse_invoice_id(raw) == expected  # SPEC.md §2: year 2000-2100 allowed


# SPEC.md Section 2: Invoice identifier - Year outside 2000-2100 -> "year out of supported range"
@pytest.mark.parametrize("raw", ["FV/1999/12/0001", "FV/2101/01/0001"])
def test_parse_invoice_id_rejects_year_out_of_range_with_specific_message_spec_section_2(raw):
    with pytest.raises(ValueError) as excinfo:
        invoice.parse_invoice_id(raw)
    assert str(excinfo.value) == "year out of supported range"  # SPEC.md §2: precise error message


# SPEC.md Section 2: Invoice identifier - Sequence number "0000" forbidden
def test_parse_invoice_id_rejects_zero_sequence_with_specific_message_spec_section_2():
    with pytest.raises(ValueError) as excinfo:
        invoice.parse_invoice_id("FV/2024/05/0000")
    assert str(excinfo.value) == "sequence number must not be zero"  # SPEC.md §2: precise error message


# SPEC.md Section 2: Invoice identifier - Format validation -> "malformed invoice id"
@pytest.mark.parametrize(
    "raw",
    [
        "FV/2024/5/0001",     # month not two digits
        "FV/2024/00/0001",    # month out of range (00)
        "FV/2024/13/0001",    # month out of range (13)
        "fv/2024/05/0001",    # lowercase prefix
        "INV/2024/05/0001",   # wrong prefix
        "FV/2024/05/001",     # seq not four digits
        "FV/2024/05/10000",   # seq five digits
        "FV/24/05/0001",      # year not four digits
        "FV//05/0001",        # missing year
        "",                   # empty
        "   ",                # only whitespace
    ],
)
def test_parse_invoice_id_rejects_malformed_inputs_with_specific_message_spec_section_2(raw):
    with pytest.raises(ValueError) as excinfo:
        invoice.parse_invoice_id(raw)
    assert str(excinfo.value) == "malformed invoice id"  # SPEC.md §2: precise error message


# SPEC.md Section 2: Invoice identifier - Month range and integer conversion in result
@pytest.mark.parametrize(
    "raw, expected_month",
    [
        ("FV/2024/01/0001", 1),
        ("FV/2024/09/0001", 9),
        ("FV/2024/12/0001", 12),
    ],
)
def test_parse_invoice_id_month_parsed_as_int_without_leading_zeros_spec_section_2(raw, expected_month):
    result = invoice.parse_invoice_id(raw)
    assert isinstance(result["month"], int)  # SPEC.md §2: int fields
    assert result["month"] == expected_month  # SPEC.md §2: no leading zeros in returned ints
