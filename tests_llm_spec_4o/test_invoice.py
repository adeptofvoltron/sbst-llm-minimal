import pytest
import invoice

# Section 1: Loyalty points - SPEC.md
def test_award_points_conversion_rate():
    # 25 PLN -> 2 points
    assert invoice.award_points(25, 0) == 2
    # 35 PLN -> 4 points due to banker's rounding
    assert invoice.award_points(35, 0) == 4
    # 24 PLN -> 2 points
    assert invoice.award_points(24, 0) == 2
    # 26 PLN -> 3 points
    assert invoice.award_points(26, 0) == 3

def test_award_points_vip_multiplier():
    # Not a VIP, 50 PLN -> 5 points
    assert invoice.award_points(50, 4999) == 5
    # VIP, 50 PLN -> 10 points
    assert invoice.award_points(50, 5000) == 10

def test_award_points_cap():
    # Without VIP, max 5000 points
    assert invoice.award_points(50000, 0) == 5000
    # With VIP, order worth 300000 PLN still yields at most 5000 points
    assert invoice.award_points(300000, 5000) == 5000

def test_award_points_validation():
    # Negative order value
    with pytest.raises(ValueError, match="amounts must not be negative"):
        invoice.award_points(-10, 0)
    # Negative lifetime spend
    with pytest.raises(ValueError, match="amounts must not be negative"):
        invoice.award_points(10, -1)

# Section 2: Invoice identifier - SPEC.md
def test_parse_invoice_id_valid():
    # Properly formatted ID
    assert invoice.parse_invoice_id("FV/2026/09/0042") == {"year": 2026, "month": 9, "seq": 42}
    # With surrounding whitespace
    assert invoice.parse_invoice_id("  FV/2026/09/0042  ") == {"year": 2026, "month": 9, "seq": 42}

def test_parse_invoice_id_invalid_format():
    with pytest.raises(ValueError, match="malformed invoice id"):
        invoice.parse_invoice_id("FV/2026/9/42")
    with pytest.raises(ValueError, match="malformed invoice id"):
        invoice.parse_invoice_id("FV/26/09/0042")

def test_parse_invoice_id_year_out_of_range():
    with pytest.raises(ValueError, match="year out of supported range"):
        invoice.parse_invoice_id("FV/1999/12/0421")
    with pytest.raises(ValueError, match="year out of supported range"):
        invoice.parse_invoice_id("FV/2101/01/0042")

def test_parse_invoice_id_sequence_number_zero():
    with pytest.raises(ValueError, match="sequence number must not be zero"):
        invoice.parse_invoice_id("FV/2023/05/0000")
