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
    
    # 1. 前年・当年・翌年の全節入り日時を取得（直前・直後の節入り判定および大運計算用）
    all_setsuiris_info = []
    for y in [target_date.year - 1, target_date.year, target_date.year + 1]:
        for m in range(1, 13):
            dt_jst = engine.get_setsuiri_jst_by_month(y, m)
            if dt_jst:
                dt_naive = dt_jst.replace(tzinfo=None)
                all_setsuiris_info.append({
                    "year": y,
                    "month": m,
                    "dt": dt_naive
                })
    
    all_setsuiris_info.sort(key=lambda x: x["dt"])
    all_setsuiris = [s["dt"] for s in all_setsuiris_info]  # 大運計算用datetimeリスト

    # 2. 当年の立春（2月の節入り）を取得して干支年（四柱推命上の年）を決定
    this_year_risshun = [s for s in all_setsuiris_info if s["year"] == target_date.year and s["month"] == 2][0]["dt"]
    kanshi_year = target_date.year - 1 if target_naive < this_year_risshun else target_date.year

    # 3. 入力日時直前の節入りを判定
    past_setsuiris = [s for s in all_setsuiris_info if s["dt"] <= target_naive]
    best_candidate = past_setsuiris[-1]
    
    setuiri_dt = best_candidate["dt"]
    elapsed_days = (target_naive - setuiri_dt).total_seconds() / 86400

    # 月インデックス（0: 寅月, 1: 卯月 ... 11: 丑月）
    current_month_idx = (best_candidate["month"] - 2) % 12

    # 4. 各柱の干支を算出
    y_stem, y_branch = KanshiEngine.get_year_kanshi(kanshi_year)
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

    # 5. 大運データ計算
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
            "time_unknown": time_unknown
        },
        "is_time_unknown": time_unknown,  # 👈 ここにトップレベルのフラグを追加
        "pillars": pillars_data,
        "kuubo": kuubo,
        "daun": daun_list
    }
    
    # 6. 深層分析（五行・身強身弱）
    from core.gogyo_engine import GogyoEngine
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
    
    if "analysis" in data:
        an = data["analysis"]
        print("\n--- 五行バランス分析（得点詳細） ---")
        gogyo_scores = an.get("gogyo_balance", {})
        
        # 各五行のスコアを少数点第1位までフォーマットして表示
        formatted_scores = [f"{k}: {float(v):.1f}点" for k, v in gogyo_scores.items()]
        print("五行スコア : " + " | ".join(formatted_scores))
        
        print(f"日干五行   : {an.get('day_stem_element', '不明')}")
        print(f"エネルギー : 自党(比劫・印星) {an.get('jitou_score', 0):.1f}点  vs  異党(食傷・財・官) {an.get('itau_score', 0):.1f}点")
        print(f"命式判定   : 【{an.get('judgment', '不明')}】")

    print("\n--- 大運 ---")
    for d in data['daun']:
        if "error" in d:
            print(f"大運エラー: {d['error']}")
        else:
            print(f" {d['start_age']:2d}歳〜 : {d['ganzhi']} ({d['tenkan_hensei']}) | {d['juniun']}")

if __name__ == "__main__":
    if not os.path.exists("output"):
        os.makedirs("output")

    # テスト1: 1961年1月4日（立春前）
    print("=== テスト1: 1961年1月4日（立春前） ===")
    target1 = datetime(1961, 1, 4, 12, 0)
    meishiki1 = get_meishiki_data(target1, gender="男", time_unknown=True)
    print_meishiki(meishiki1)
    
    print("\n" + "="*40 + "\n")

    # テスト2: 通常の日時
    print("=== テスト2: 1981年10月15日 ===")
    target2 = datetime(1981, 10, 15, 5, 0)
    meishiki2 = get_meishiki_data(target2, gender="女", time_unknown=False)
    print_meishiki(meishiki2)