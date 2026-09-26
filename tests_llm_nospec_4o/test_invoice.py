import pytest
import invoice

def test_valid_invoice_id():
    valid_id = "FV/2023/09/0001"
    result = invoice.parse_invoice_id(valid_id)
    assert result == {"year": 2023, "month": 9, "seq": 1}

def test_invalid_invoice_id_format():
    with pytest.raises(ValueError, match="malformed invoice id"):
        invoice.parse_invoice_id("FV-2023-09-0001")
    with pytest.raises(ValueError, match="malformed invoice id"):
        invoice.parse_invoice_id("FV/2023/13/0001")
    with pytest.raises(ValueError, match="malformed invoice id"):
        invoice.parse_invoice_id("FV/20a3/09/0001")

def test_year_out_of_range():
    with pytest.raises(ValueError, match="year out of supported range"):
        invoice.parse_invoice_id("FV/1999/09/0001")
    with pytest.raises(ValueError, match="year out of supported range"):
        invoice.parse_invoice_id("FV/2101/09/0001")

def test_zero_sequence_number():
    with pytest.raises(ValueError, match="sequence number must not be zero"):
        invoice.parse_invoice_id("FV/2023/09/0000")

def test_strip_whitespace():
    valid_id_with_spaces = "  FV/2023/09/0001  "
    result = invoice.parse_invoice_id(valid_id_with_spaces)
    assert result == {"year": 2023, "month": 9, "seq": 1}
