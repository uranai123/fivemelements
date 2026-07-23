# -*- coding: utf-8 -*-
import json
import os
from datetime import datetime
from core.kanshi import KanshiEngine
from core.zokan_engine import ZokanEngine
from core.hensei_engine import HenseiEngine
from core.juniun_engine import JuniunEngine
from core.daiun_engine import DaunCalculator
from core.kubo import get_kuubo
from solar_engine import SolarEngine

def get_meishiki_data(target_date: datetime, gender: str = "男", time_unknown: bool = False):
    """
    計算ロジックを統合し、全データを辞書（dict）で返す関数
    time_unknown=True の場合、時柱を除外した「三柱推命」として処理します。
    """
    target_naive = target_date.replace(tzinfo=None) if target_date.tzinfo is not None else target_date
    engine = SolarEngine()
    
    # 1. 節入り日時の全件取得
    all_setsuiris = []
    candidates = []
    for m_idx in range(12):
        dt_jst = engine.get_setsuiri_jst(target_date.year, m_idx)
        if dt_jst:
            dt_naive = dt_jst.replace(tzinfo=None)
            all_setsuiris.append(dt_naive)
            candidates.append({"index": m_idx, "dt": dt_naive})
    
    # 2. 命式の算出
    valid_candidates = [c for c in candidates if c["dt"] <= target_naive]
    valid_candidates.sort(key=lambda x: x["dt"])
    best_candidate = valid_candidates[-1] if valid_candidates else candidates[0]
    
    current_month_idx = best_candidate["index"]
    setuiri_dt = best_candidate["dt"]
    elapsed_days = (target_naive - setuiri_dt).total_seconds() / 86400

    y_stem, y_branch = KanshiEngine.get_year_kanshi(target_date.year)
    m_stem, m_branch = KanshiEngine.get_month_kanshi(y_stem, current_month_idx)
    d_stem, d_branch = KanshiEngine.get_day_kanshi(target_naive)

    # 時柱の算出（時刻不明の場合はスキップ）
    if not time_unknown:
        h_stem, h_branch = KanshiEngine.get_hour_kanshi(d_stem, target_naive.hour)

    day_ganshi_str = KanshiEngine.TENKAN[d_stem] + KanshiEngine.CHISHI[d_branch]
    kuubo = get_kuubo(day_ganshi_str)

    day_stem_ref = d_stem
    
    # 基本の3柱（年・月・日）をセット
    pillars_raw = [
        {"name": "年", "s_idx": y_stem, "b_idx": y_branch},
        {"name": "月", "s_idx": m_stem, "b_idx": m_branch},
        {"name": "日", "s_idx": d_stem, "b_idx": d_branch},
    ]
    
    # 時刻が判明している場合のみ時柱を追加
    if not time_unknown:
        pillars_raw.append({"name": "時", "s_idx": h_stem, "b_idx": h_branch})

    # データ構造の構築
    pillars_data = []
    for p in pillars_raw:
        stem_char = KanshiEngine.TENKAN[p["s_idx"]]
        stem_hensei = "－" if p["name"] == "日" else HenseiEngine.get_hensei(day_stem_ref, p["s_idx"])
        
        branch_char = KanshiEngine.CHISHI[p["b_idx"]]
        zokan_char = ZokanEngine.get_zokan_from_diff(branch_char, elapsed_days)
        zokan_hensei = HenseiEngine.get_hensei(day_stem_ref, KanshiEngine.TENKAN.index(zokan_char))
        
        stem_juniun = JuniunEngine.get_juniun(day_stem_ref, p["b_idx"])
        
        pillars_data.append({
            "name": p["name"],
            "stem": stem_char,
            "stem_hensei": stem_hensei,
            "branch": branch_char,
            "zokan": zokan_char,
            "zokan_hensei": zokan_hensei,
            "juniun": stem_juniun
        })
        
    # UI側の表示が崩れないよう、時柱不明の場合は「空の時柱データ」をダミーで末尾に追加してあげるのも親切です。
    # ここでは、pillars_data には純粋に存在する柱だけを持たせ、メタデータに三柱モードであることを記録します。

    # 大運データ（大運は日柱・月柱から算出するため、出生時刻が不明でも計算可能です！）
    daun_list = []
    try:
        daun_raw = DaunCalculator.calculate_daun(target_naive, all_setsuiris, gender, y_stem, m_stem, m_branch)
        for d in daun_raw:
            daun_list.append({
                "start_age": d['start_age'],
                "ganzhi": d['ganzhi'],
                "tenkan_hensei": HenseiEngine.get_hensei(day_stem_ref, d['s_idx']),
                "juniun": JuniunEngine.get_juniun(day_stem_ref, d['b_idx'])
            })
    except Exception as e:
        daun_list = [{"error": str(e)}]

    meishiki_result = {
        "metadata": {
            "date": target_date.strftime('%Y-%m-%d %H:%M'), 
            "gender": gender,
            "time_unknown": time_unknown  # 三柱推命フラグを保持
        },
        "pillars": pillars_data,
        "kuubo": kuubo,
        "daun": daun_list
    }
    
    # --- Phase 2: 深層分析の追加 ---
    from core.gogyo_engine import GogyoEngine
    # GogyoEngine が pillars の数を動的に見て計算してくれる設計であれば、このまま渡せば3柱分でスコアを出してくれます。
    analysis = GogyoEngine.analyze_meishiki_gogyo(meishiki_result)
    meishiki_result["analysis"] = analysis
    
    return meishiki_result

def print_meishiki(data):
    """画面表示用のフォーマッター"""
    is_three_pillars = data['metadata'].get('time_unknown', False)
    mode_name = "三柱推命" if is_three_pillars else "四柱推命"
    
    print(f"--- {data['metadata']['date']} ({data['metadata']['gender']}) の命式 [{mode_name}] ---")
    print("柱 | 天干(通変) | 地支(蔵干:通変) | 12運")
    print("------------------------------------------")
    for p in data['pillars']:
        print(f"{p['name']} | {p['stem']}({p['stem_hensei']}) | {p['branch']}({p['zokan']}:{p['zokan_hensei']}) | {p['juniun']}")
    print(f"\n空亡: {data['kuubo']}")
    
    # 五行・身強身弱の表示
    if "analysis" in data:
        an = data["analysis"]
        print("\n--- 五行バランス分析 ---")
        balance_str = " | ".join([f"{k}: {v}" for k, v in an["gogyo_balance"].items()])
        print(f"五行スコア : {balance_str}")
        print(f"日干五行   : {an['day_stem_element']}")
        print(f"エネルギー : 自党(比劫・印星) {an['jitou_score']}  vs  異党(食傷・財・官) {an['itau_score']}")
        print(f"命式判定   : 【{an['judgment']}】")

    print("\n--- 大運 ---")
    for d in data['daun']:
        if "error" in d:
            print(f"大運エラー: {d['error']}")
        else:
            print(f" {d['start_age']:2d}歳〜 : {d['ganzhi']} ({d['tenkan_hensei']}) | {d['juniun']}")

if __name__ == "__main__":
    if not os.path.exists("output"):
        os.makedirs("output")

    # テスト1: 通常の四柱推命
    print("=== テスト1: 四柱推命（時刻あり） ===")
    target = datetime(1981, 10, 15, 5, 0)
    meishiki_four = get_meishiki_data(target, gender="女", time_unknown=False)
    print_meishiki(meishiki_four)
    
    print("\n" + "="*40 + "\n")

    # テスト2: 出生時刻不明（三柱推命）
    print("=== テスト2: 三柱推命（時刻不明） ===")
    meishiki_three = get_meishiki_data(target, gender="女", time_unknown=True)
    print_meishiki(meishiki_three)
    
    # JSON保存（確認用）
    with open("output/meishiki_data_three_pillars.json", "w", encoding="utf-8") as f:
        json.dump(meishiki_three, f, ensure_ascii=False, indent=4)