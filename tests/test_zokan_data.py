import pytest
from core.zokan_data import ZOKAN_MAP

def test_zokan_map_total_days():
    """各地支の蔵干日数の合計が30日（または暦上の1ヶ月の長さ）になっているか検証"""
    # 四柱推命において、節入りから次の節入りまでは概ね30日程度
    # ここでは合計が30であることを正とするバリデーション
    for branch, periods in ZOKAN_MAP.items():
        total_days = sum(days for stem, days in periods)
        assert total_days == 30, f"{branch} の蔵干合計日数が30ではありません (合計: {total_days})"

def test_zokan_map_format():
    """データ構造が正しいか（タプルで、2番目が数値か）を確認"""
    for branch, periods in ZOKAN_MAP.items():
        assert isinstance(periods, list), f"{branch} はリストである必要があります"
        for item in periods:
            assert isinstance(item, tuple), f"{branch} の各項目はタプルである必要があります"
            assert isinstance(item[1], int), f"{branch} の日数は整数である必要があります"

@pytest.mark.parametrize("branch", ZOKAN_MAP.keys())
def test_zokan_map_not_empty(branch):
    """すべての地支にデータが存在することを確認"""
    assert len(ZOKAN_MAP[branch]) > 0, f"{branch} にデータがありません"