# tests/test_zokan_engine.py
import pytest
import datetime
from core.zokan_engine import ZokanEngine

# テストデータ: 実際の ZOKAN_MAP に合わせて調整してください
# 例として「寅」の想定（戊, 丙, 甲の順で日数が決まっていると仮定）
class TestZokanEngine:

    @pytest.mark.parametrize("branch, elapsed_days, expected", [
        ("寅", 0, "戊"),   # 期間の開始日
        ("寅", 6, "戊"),   # 6日目はまだ「戊」
        ("寅", 7, "丙"),   # 7日目で「丙」に切り替わる
        ("寅", 15, "甲"),  # 期間の後半
    ])
    def test_get_zokan_from_diff(self, branch, elapsed_days, expected):
        """経過日数からの判定ロジックをテスト"""
        result = ZokanEngine.get_zokan_from_diff(branch, elapsed_days)
        assert result == expected

    def test_get_zokan_date_logic(self):
        """日付計算を含めた蔵干判定をテスト"""
        # 寅月（節入り）を想定
        solar_term = datetime.datetime(2026, 2, 4) # 立春
        target = datetime.datetime(2026, 2, 5)     # 経過1日
        
        # 1日経過なら最初の蔵干（戊）になるはず
        result = ZokanEngine.get_zokan("寅", target, solar_term)
        assert result == "戊"

    def test_invalid_branch(self):
        """不正な地支が渡された場合の挙動（エラーハンドリング）"""
        # 必要に応じて、例外を投げるかどうかのテストを追加
        with pytest.raises(ValueError):
            ZokanEngine.get_zokan("架空の地支", datetime.datetime.now(), datetime.datetime.now())