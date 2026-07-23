# -*- coding: utf-8 -*-
from .zokan_data import ZOKAN_MAP
import datetime

class ZokanEngine:
    # --- 既存のメソッド（デバッグ機能付き）: そのまま残します ---
    @staticmethod
    def get_zokan(branch: str, target_date: datetime.datetime, solar_term_date: datetime.datetime):
        periods = ZOKAN_MAP.get(branch)
        if not periods:
            raise ValueError(f"不明な地支です: {branch}")
        
        diff = target_date - solar_term_date
        days_diff = diff.total_seconds() / 86400
        
        print(f"[DEBUG] 蔵干判定: {branch}")
        print(f"  ターゲット日時: {target_date}")
        print(f"  節入り日時    : {solar_term_date}")
        print(f"  経過日数(diff): {days_diff:.2f} 日")

        current_day_limit = 0
        for stem, duration in periods:
            current_day_limit += duration
            if days_diff < current_day_limit:
                print(f"  -> 判定結果: {stem} (判定閾値: {current_day_limit}日)")
                return stem
        
        result = periods[-1][0]
        print(f"  -> 判定結果(範囲外): {result}")
        return result

    # --- 新しく追加するメソッド（共通ロジック用） ---
    @staticmethod
    def get_zokan_from_diff(branch_name, elapsed_days):
        """
        経過日数(elapsed_days)だけを渡して判定するシンプルなメソッド
        """
        if branch_name not in ZOKAN_MAP:
            return "不明"
        
        # 累積日数を計算しながら対象の蔵干を探す
        cumulative = 0
        for stem, days in ZOKAN_MAP[branch_name]:
            cumulative += days
            if elapsed_days < cumulative:
                return stem
        
        # 範囲を超えた場合は最後の蔵干を返す
        return ZOKAN_MAP[branch_name][-1][0]