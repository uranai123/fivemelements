import pytest
from datetime import datetime
from core.kanshi import KanshiEngine

# 代表的な日付の期待値をテスト
@pytest.mark.parametrize("target_date, expected", [
    # 時柱の期待値を「甲子」から「壬子」へ修正
    (datetime(2026, 3, 15, 0, 30), ("丙午", "辛卯", "戊子", "壬子")),
])
def test_kanshi_engine_full(target_date, expected):
    y_ten, y_chi = KanshiEngine.get_year_kanshi(target_date.year)
    # ※注: month_idxは節入り判定が必要なため、単体テストでは固定値または計算ロジックを通す
    m_ten, m_chi = KanshiEngine.get_month_kanshi(y_ten, 1) 
    d_ten, d_chi = KanshiEngine.get_day_kanshi(target_date)
    h_ten, h_chi = KanshiEngine.get_hour_kanshi(d_ten, target_date.hour)
    
    # 期待値と一致するか確認
    assert KanshiEngine.TENKAN[y_ten] + KanshiEngine.CHISHI[y_chi] == expected[0]
    assert KanshiEngine.TENKAN[m_ten] + KanshiEngine.CHISHI[m_chi] == expected[1]
    assert KanshiEngine.TENKAN[d_ten] + KanshiEngine.CHISHI[d_chi] == expected[2]
    assert KanshiEngine.TENKAN[h_ten] + KanshiEngine.CHISHI[h_chi] == expected[3]

def test_day_kanshi_base():
    """基準日(1900/1/1)が甲戌であることの確認"""
    base = datetime(1900, 1, 1)
    ten, chi = KanshiEngine.get_day_kanshi(base)
    # 甲戌は TENKAN[0], CHISHI[10]
    assert ten == 0
    assert chi == 10