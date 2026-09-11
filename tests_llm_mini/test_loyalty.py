import pytest
import loyalty

def test_award_points_basic():
    # Test for regular points (SPEC.md section 1)
    assert loyalty.award_points(100, 0) == 10
    assert loyalty.award_points(250, 0) == 25
    assert loyalty.award_points(99.99, 0) == 9
    assert loyalty.award_points(10, 0) == 1

def test_award_points_rounding():
    # Test for banker's rounding (SPEC.md section 1)
    assert loyalty.award_points(2.5, 0) == 2
    assert loyalty.award_points(3.5, 0) == 4
    assert loyalty.award_points(2.4, 0) == 2
    assert loyalty.award_points(2.6, 0) == 3

def test_award_points_vip_multiplier():
    # Test for VIP multiplier (SPEC.md section 1)
    assert loyalty.award_points(100, 5001) == 20  # 10 points * 2
    assert loyalty.award_points(100, 5000) == 10  # No multiplier
    assert loyalty.award_points(1000, 5001) == 200  # 100 points * 2 
    assert loyalty.award_points(5000, 6000) == 5000  # Capped at 5000 after multiplier

def test_award_points_cap():
    # Test for points cap (SPEC.md section 1)
    assert loyalty.award_points(60000, 10000) == 5000  # Capped
    assert loyalty.award_points(50000, 6000) == 5000  # Capped

def test_award_points_validation():
    # Test for validation (SPEC.md section 1)
    with pytest.raises(ValueError, match="amounts must not be negative"):
        loyalty.award_points(-1, 0)
    with pytest.raises(ValueError, match="amounts must not be negative"):
        loyalty.award_points(0, -1)
