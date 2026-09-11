import pytest
import invoice

def test_parse_invoice_id_valid():
    # Test for valid invoice ID (SPEC.md section 2)
    assert invoice.parse_invoice_id("FV/2026/09/0042") == {"year": 2026, "month": 9, "seq": 42}
    assert invoice.parse_invoice_id(" FV/2023/01/0010 ") == {"year": 2023, "month": 1, "seq": 10}

def test_parse_invoice_id_malformed():
    # Test for malformed invoice ID (SPEC.md section 2)
    with pytest.raises(ValueError, match="malformed invoice id"):
        invoice.parse_invoice_id("INVALID/2023/01/0010")
    with pytest.raises(ValueError, match="malformed invoice id"):
        invoice.parse_invoice_id("FV/202312/0010")
    
def test_parse_invoice_id_year_out_of_range():
    # Test for year out of range (SPEC.md section 2)
    with pytest.raises(ValueError, match="year out of supported range"):
        invoice.parse_invoice_id("FV/1999/01/0001")
    with pytest.raises(ValueError, match="year out of supported range"):
        invoice.parse_invoice_id("FV/2101/01/0001")

def test_parse_invoice_id_sequence_number_zero():
    # Test for sequence number equal to '0000' (SPEC.md section 2)
    with pytest.raises(ValueError, match="sequence number must not be zero"):
        invoice.parse_invoice_id("FV/2023/01/0000")
