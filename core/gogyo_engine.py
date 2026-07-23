# -*- coding: utf-8 -*-

class GogyoEngine:
    # 五行の定義
    ELEMENTS = ["木", "火", "土", "金", "水"]
    
    # 十干の五行属性
    STEM_MAP = {
        "甲": "木", "乙": "木",
        "丙": "火", "丁": "火",
        "戊": "土", "己": "土",
        "庚": "金", "辛": "金",
        "壬": "水", "癸": "水"
    }
    
    # 十二支の五行属性（蔵干を考慮したメイン属性）
    BRANCH_MAP = {
        "寅": "木", "卯": "木",
        "巳": "火", "午": "火",
        "辰": "土", "戌": "土", "丑": "土", "未": "土",
        "申": "金", "酉": "金",
        "亥": "水", "子": "水"
    }

    # 旺相休囚の係数（季節ごとの五行の強さ）
    SEASON_WEIGHTS = {
        "木": {"春": 1.5, "夏": 0.8, "秋": 0.5, "冬": 1.2},
        "火": {"春": 1.2, "夏": 1.5, "秋": 0.8, "冬": 0.5},
        "土": {"春": 0.8, "夏": 1.2, "秋": 1.0, "冬": 0.8},
        "金": {"春": 0.5, "夏": 0.8, "秋": 1.5, "冬": 1.2},
        "水": {"春": 0.8, "夏": 0.5, "秋": 1.2, "冬": 1.5},
    }

    @classmethod
    def get_element(cls, kan_or_shi):
        return cls.STEM_MAP.get(kan_or_shi) or cls.BRANCH_MAP.get(kan_or_shi)

    @classmethod
    def calculate_energy(cls, kan_or_shi, month_branch):
        """指定された干支の、月支に基づくエネルギーを算出"""
        element = cls.get_element(kan_or_shi)
        month_element = cls.BRANCH_MAP.get(month_branch)
        
        # 月支から季節を簡易判定
        season = "春" if month_element in ["木"] else \
                 "夏" if month_element in ["火"] else \
                 "秋" if month_element in ["金"] else "冬"
        
        return cls.SEASON_WEIGHTS[element][season]

    @classmethod
    def analyze_meishiki_gogyo(cls, meishiki_data):
        """
        命式JSONデータを受け取り、五行バランスの集計と簡易的な身強・身弱を判定する
        """
        pillars = meishiki_data.get("pillars", [])
        
        # 1. 月支（季節の基準）と日干（自分自身）を特定
        month_branch = None
        day_stem = None
        for p in pillars:
            if p["name"] == "月":
                month_branch = p["branch"]
            if p["name"] == "日":
                day_stem = p["stem"]
                
        if not month_branch or not day_stem:
            raise ValueError("月支または日干が命式データ内に見つかりません。")
            
        # 五行スコアの初期化
        gogyo_scores = {el: 0.0 for el in cls.ELEMENTS}
        
        # 2. 各柱の天干・地支のエネルギーを集計
        for p in pillars:
            # 天干の集計
            stem_el = cls.STEM_MAP.get(p["stem"])
            if stem_el:
                gogyo_scores[stem_el] += cls.calculate_energy(p["stem"], month_branch)
                
            # 地支の集計（算出済みの蔵干をベースに集計）
            zokan_el = cls.STEM_MAP.get(p["zokan"])
            if zokan_el:
                gogyo_scores[zokan_el] += cls.calculate_energy(p["zokan"], month_branch)

        # 3. 身強・身弱の判定（自党 vs 異党）
        day_stem_el = cls.STEM_MAP.get(day_stem)
        
        # 相生関係から、日干を生じる五行（印星）のインデックスを取得
        day_el_idx = cls.ELEMENTS.index(day_stem_el)
        hibo_el = day_stem_el                         # 比劫（自分と同じ五行）
        insei_el = cls.ELEMENTS[(day_el_idx - 1) % 5] # 印星（自分を生み出す一つ前の五行）
        
        # 自党（自分を助けるエネルギー）の合計
        jitou_score = gogyo_scores[hibo_el] + gogyo_scores[insei_el]
        # 異党（自分のエネルギーを漏らす・剋されるエネルギー）の合計
        itau_score = sum(gogyo_scores.values()) - jitou_score
        
        # スコアの丸め処理
        gogyo_balance_rounded = {k: round(v, 2) for k, v in gogyo_scores.items()}
        jitou_score = round(jitou_score, 2)
        itau_score = round(itau_score, 2)
        
        # 判定
        judgment = "身強" if jitou_score >= itau_score else "身弱"
        
        return {
            "gogyo_balance": gogyo_balance_rounded,
            "day_stem_element": day_stem_el,
            "jitou_score": jitou_score,
            "itau_score": itau_score,
            "judgment": judgment
        }