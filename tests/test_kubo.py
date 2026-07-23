import pytest
from core.kubo import get_kuubo
from core.kubo import KUUBO_MAP

@pytest.mark.parametrize("ganshi, expected", [
    # 各グループから代表値をテスト
    ("甲寅", "子丑"),
    ("癸亥", "子丑"),
    ("甲辰", "寅卯"),
    ("癸丑", "寅卯"),
    ("甲午", "辰巳"),
    ("癸卯", "辰巳"),
    ("甲申", "午未"),
    ("癸巳", "午未"),
    ("甲戌", "申酉"),
    ("癸未", "申酉"),
    ("甲子", "戌亥"),
    ("癸酉", "戌亥"),
])
def test_get_kuubo_valid(ganshi, expected):
    """正常系のテスト：正しい空亡が返るか"""
    assert get_kuubo(ganshi) == expected

def test_get_kuubo_invalid():
    """異常系のテスト：存在しない干支が渡されたら '不明' が返るか"""
    assert get_kuubo("存在しない干支") == "不明"
    
def test_kuubo_map_completeness():
    """KUUBO_MAPのデータが60個すべて揃っているか確認"""
    assert len(KUUBO_MAP) == 60, f"干支は60個あるはずですが、{len(KUUBO_MAP)}個しかありません"