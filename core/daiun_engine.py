# -*- coding: utf-8 -*-
from datetime import datetime
import math

class DaunCalculator:
    GANZHI_TABLE = [
        "甲子", "乙丑", "丙寅", "丁卯", "戊辰", "己巳", "庚午", "辛未", "壬申", "癸酉",
        "甲戌", "乙亥", "丙子", "丁丑", "戊寅", "己卯", "庚辰", "辛巳", "壬午", "癸未",
        "甲申", "乙酉", "丙戌", "丁亥", "戊子", "己丑", "庚寅", "辛卯", "壬辰", "癸巳",
        "甲午", "乙未", "丙申", "丁酉", "戊戌", "己亥", "庚子", "辛丑", "壬寅", "癸卯",
        "甲辰", "乙巳", "丙午", "丁未", "戊申", "己酉", "庚戌", "辛亥", "壬子", "癸丑",
        "甲寅", "乙卯", "丙辰", "丁巳", "戊午", "己未", "庚申", "辛酉", "壬戌", "癸亥"
    ]

    # ... (get_direction, get_target_setsuiri は変更なし) ...
    @staticmethod
    def get_direction(gender, year_stem_idx):
        is_yang = (year_stem_idx % 2 == 0)
        is_male = (gender == "男")
        return 1 if (is_male and is_yang) or (not is_male and not is_yang) else -1

    @staticmethod
    def get_target_setsuiri(birth_time, setsuiri_list, direction):
        sorted_list = sorted(setsuiri_list)
        if direction == 1:
            candidates = [dt for dt in sorted_list if dt >= birth_time]
            return candidates[0] if candidates else None
        else:
            candidates = [dt for dt in sorted_list if dt <= birth_time]
            return candidates[-1] if candidates else None

    @staticmethod
    def calculate_daun(birth_time, setsuiri_list, gender, year_stem_idx, month_stem_idx, month_branch_idx):
        direction = DaunCalculator.get_direction(gender, year_stem_idx)
        target_setsuiri = DaunCalculator.get_target_setsuiri(birth_time, setsuiri_list, direction)
        if not target_setsuiri:
            raise ValueError("適切な節入りが見つかりませんでした。")
            
        diff_days = abs((target_setsuiri - birth_time).total_seconds()) / 86400
        age_of_onset = round(diff_days / 3)
        
        # 🌟 修正：起運年齢が0歳（1年未満）の場合は、1歳立運に切り上げる
        if age_of_onset < 1:
            age_of_onset = 1
        
        month_pillar_idx = (month_stem_idx * 6 - month_branch_idx * 5) % 60
        
        daun_list = []
        
        # 0番目: 0歳〜 (月柱)
        daun_list.append({
            "start_age": 0,
            "ganzhi": DaunCalculator.GANZHI_TABLE[month_pillar_idx],
            "s_idx": month_pillar_idx % 10,
            "b_idx": month_pillar_idx % 12
        })
        
        # 1〜9番目: 起運年齢以降
        for i in range(1, 10):
            idx = (month_pillar_idx + (direction * i)) % 60
            daun_list.append({
                "start_age": age_of_onset + ((i - 1) * 10),
                "ganzhi": DaunCalculator.GANZHI_TABLE[idx],
                "s_idx": idx % 10,
                "b_idx": idx % 12
            })
            
        return daun_list