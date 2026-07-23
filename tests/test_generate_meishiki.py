import pytest
from datetime import datetime
from generate_meishiki4 import get_meishiki_data

def test_get_meishiki_data_integration():
    # 1. テスト用の入力データ（1996-08-20 19:20 男）
    target = datetime(1996, 8, 20, 19, 20)
    
    # 2. マスター関数を実行
    result = get_meishiki_data(target, gender="男")
    
    # 3. 重要なデータポイントを検証（アサーション）
    assert result["metadata"]["gender"] == "男"
    assert result["kuubo"] == "午未"
    
    # 年柱が正しいか (丙子)
    year_pillar = next(p for p in result["pillars"] if p["name"] == "年")
    assert year_pillar["stem"] == "丙"
    assert year_pillar["branch"] == "子"
    
    # 大運のデータが存在するか
    assert len(result["daun"]) > 0