import pytest
from datetime import datetime
from core.daiun_engine import DaunCalculator

def test_calculate_daun_basic():
    birth = datetime(2026, 7, 9, 11, 0)
    setsuiri = [datetime(2026, 7, 12, 11, 0)]
    result = DaunCalculator.calculate_daun(birth, setsuiri, "男", 0, 1, 1)
    
    assert result[0]["start_age"] == 0
    assert result[1]["start_age"] == 1
    assert result[1]["ganzhi"] != result[0]["ganzhi"]

def test_get_direction():
    assert DaunCalculator.get_direction("男", 0) == 1
    assert DaunCalculator.get_direction("男", 1) == -1
    assert DaunCalculator.get_direction("女", 0) == -1
    assert DaunCalculator.get_direction("女", 1) == 1

def test_calculate_daun_boundary_age():
    birth = datetime(2026, 7, 9, 11, 0)
    setsuiri_1 = [datetime(2026, 7, 11, 0, 0)] 
    setsuiri_2 = [datetime(2026, 7, 9, 23, 0)]
    
    result_1 = DaunCalculator.calculate_daun(birth, setsuiri_1, "男", 0, 1, 1)
    result_2 = DaunCalculator.calculate_daun(birth, setsuiri_2, "男", 0, 1, 1)
    
    assert result_1[1]["start_age"] == 1
    assert result_2[1]["start_age"] == 0

def test_calculate_daun_with_real_data():
    birth = datetime(1996, 8, 20, 19, 20)
    setsuiri_list = [
        datetime(1996, 8, 7, 0, 0),
        datetime(1996, 9, 7, 0, 0)
    ]
    result = DaunCalculator.calculate_daun(birth, setsuiri_list, "男", 2, 2, 8)
    assert result[1]["start_age"] == 6