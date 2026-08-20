# -*- coding: utf-8 -*-


class GogyoEngine:
    ELEMENTS = ["木", "火", "土", "金", "水"]

    STEM_MAP = {
        "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
        "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
    }

    BRANCH_MAP = {
        "寅": "木", "卯": "木", "巳": "火", "午": "火",
        "辰": "土", "戌": "土", "丑": "土", "未": "土",
        "申": "金", "酉": "金", "亥": "水", "子": "水",
    }

    EL_STEMS = {
        "木": ["甲", "乙"], "火": ["丙", "丁"], "土": ["戊", "己"],
        "金": ["庚", "辛"], "水": ["壬", "癸"],
    }

    KOKU_MAP = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

    # 対衝（六衝）の定義
    OPPOSING_CLASHES = {
        ("子", "午"), ("午", "子"),
        ("卯", "酉"), ("酉", "卯"),
        ("寅", "申"), ("申", "寅"),
        ("巳", "亥"), ("亥", "巳"),
        ("辰", "戌"), ("戌", "辰"),
        ("丑", "未"), ("未", "丑"),
    }

    ZOKAN_DETAIL = {
        "子": [("癸", 1.0)],
        "丑": [("己", 0.6), ("癸", 0.3), ("辛", 0.1)],
        "寅": [("甲", 0.6), ("丙", 0.3), ("戊", 0.1)],
        "卯": [("乙", 1.0)],
        "辰": [("戊", 0.6), ("乙", 0.3), ("癸", 0.1)],
        "巳": [("丙", 0.6), ("庚", 0.3), ("戊", 0.1)],
        "午": [("丁", 0.7), ("己", 0.3)],
        "未": [("己", 0.6), ("丁", 0.3), ("乙", 0.1)],
        "申": [("庚", 0.6), ("壬", 0.3), ("戊", 0.1)],
        "酉": [("辛", 1.0)],
        "戌": [("戊", 0.6), ("辛", 0.3), ("丁", 0.1)],
        "亥": [("壬", 0.7), ("甲", 0.3)],
    }

    BASE_SEASON_WEIGHTS = {
        "木": {"春": 1.5, "夏": 0.8, "土用": 0.7, "秋": 0.4, "冬": 1.2},
        "火": {"春": 1.2, "夏": 1.5, "土用": 0.7, "秋": 0.7, "冬": 0.4},
        "土": {"春": 0.5, "夏": 1.2, "土用": 1.5, "秋": 0.8, "冬": 0.5},
        "金": {"春": 0.4, "夏": 0.5, "土用": 1.3, "秋": 1.5, "冬": 0.9},
        "水": {"春": 0.7, "夏": 0.3, "土用": 0.5, "秋": 1.3, "冬": 1.5},
    }

    @classmethod
    def _get_season(cls, month_branch):
        if month_branch in ["寅", "卯"]:
            return "春"
        elif month_branch in ["巳", "午"]:
            return "夏"
        elif month_branch in ["辰", "未", "戌", "丑"]:
            return "土用"
        elif month_branch in ["申", "酉"]:
            return "秋"
        elif month_branch in ["亥", "子"]:
            return "冬"
        return "春"

    @classmethod
    def _detect_goka_bonuses(cls, branches, other_stems, month_branch):
        """
        日干を除外した他天干(年・月・時)および月令による透出検証を行い、
        合化条件に応じた「加算用ボーナススコア」を算出する。
        """
        valid_branches = [b for b in branches if b in cls.BRANCH_MAP]
        bonuses = {el: 0.0 for el in cls.ELEMENTS}

        sankai_map = {
            ("寅", "卯", "辰"): ("木", 2.5),
            ("巳", "午", "未"): ("火", 2.5),
            ("申", "酉", "戌"): ("金", 2.5),
            ("亥", "子", "丑"): ("水", 2.5),
        }
        sango_map = {
            ("亥", "卯", "未"): ("木", 2.0),
            ("寅", "午", "戌"): ("火", 2.0),
            ("巳", "酉", "丑"): ("金", 2.0),
            ("申", "子", "辰"): ("水", 2.0),
        }
        hankai_map = {
            ("寅", "午"): ("火", 1.2), ("午", "戌"): ("火", 1.2),
            ("亥", "卯"): ("木", 1.2), ("卯", "未"): ("木", 1.2),
            ("巳", "酉"): ("金", 1.2), ("酉", "丑"): ("金", 1.2),
            ("申", "子"): ("水", 1.2), ("子", "辰"): ("水", 1.2),
        }

        # 1. 三会・三合の判定
        matched = False
        for combo, (target_el, base_bonus) in {**sankai_map, **sango_map}.items():
            if all(b in valid_branches for b in combo):
                has_toushutsu = any(s in cls.EL_STEMS.get(target_el, []) for s in other_stems)
                has_getsurei_support = cls.BRANCH_MAP.get(month_branch) == target_el

                if has_toushutsu or has_getsurei_support:
                    bonuses[target_el] += base_bonus
                    matched = True

        # 2. 三会・三合が不成立の場合のみ半合を判定
        if not matched:
            for combo, (target_el, base_bonus) in hankai_map.items():
                if all(b in valid_branches for b in combo):
                    has_toushutsu = any(s in cls.EL_STEMS.get(target_el, []) for s in other_stems)
                    has_getsurei_support = cls.BRANCH_MAP.get(month_branch) == target_el

                    if has_toushutsu or has_getsurei_support:
                        bonuses[target_el] += base_bonus

        return bonuses

    @classmethod
    def _calculate_clash_factors(cls, branches):
        """
        地支間の対衝(七衝)を検出し、地支間の距離(隣接・隔柱・遠隔)と
        五行の相剋関係に基づいて減衰係数を動的に算出する。
        - 距離1 (隣接)   : 勝者 0.8倍 / 敗者 0.5倍
        - 距離2 (1柱離れ): 勝者 0.9倍 / 敗者 0.75倍
        - 距離3 (年と時) : 勝者 0.95倍 / 敗者 0.9倍
        """
        factors = [1.0] * len(branches)
        n = len(branches)

        for i in range(n):
            for j in range(i + 1, n):
                b1, b2 = branches[i], branches[j]
                if (b1, b2) in cls.OPPOSING_CLASHES:
                    distance = abs(i - j)
                    if distance == 1:
                        loser_factor = 0.5
                        winner_factor = 0.8
                    elif distance == 2:
                        loser_factor = 0.75
                        winner_factor = 0.9
                    else:
                        loser_factor = 0.9
                        winner_factor = 0.95

                    el1 = cls.BRANCH_MAP.get(b1)
                    el2 = cls.BRANCH_MAP.get(b2)

                    if cls.KOKU_MAP.get(el1) == el2:
                        factors[i] *= winner_factor  # el1が勝者
                        factors[j] *= loser_factor   # el2が敗者
                    elif cls.KOKU_MAP.get(el2) == el1:
                        factors[i] *= loser_factor   # el1が敗者
                        factors[j] *= winner_factor  # el2が勝者
                    else:
                        # 土どうしの衝 (辰戌, 丑未)
                        factors[i] *= winner_factor
                        factors[j] *= winner_factor

        return factors

    @classmethod
    def analyze_meishiki_gogyo(cls, meishiki_data):
        raw_pillars = meishiki_data.get("pillars", [])
        is_unknown = meishiki_data.get("is_time_unknown", False) or meishiki_data.get("metadata", {}).get("time_unknown", False)

        pillars = []
        for p in raw_pillars:
            p_name = p.get("name")
            p_stem = p.get("stem")
            p_branch = p.get("branch")

            if is_unknown and p_name == "時":
                continue
            if p_stem in ["不明", None, ""] or p_branch in ["不明", None, ""]:
                continue

            pillars.append(p)

        stems = [p.get("stem") for p in pillars]
        branches = [p.get("branch") for p in pillars]

        day_stem = None
        month_branch = None
        other_stems = []

        for p in pillars:
            p_name = p.get("name")
            p_stem = p.get("stem")
            if p_name == "日":
                day_stem = p_stem
            else:
                other_stems.append(p_stem)  # 日干を除外した「他天干」リスト
            if p_name == "月":
                month_branch = p.get("branch")

        if not day_stem or not month_branch:
            raise ValueError("日干または月支が指定されていません。")

        day_stem_el = cls.STEM_MAP[day_stem]
        season = cls._get_season(month_branch)

        # 1. 天干のカウント
        raw_element_counts = {el: 0.0 for el in cls.ELEMENTS}
        for s in stems:
            if s in cls.STEM_MAP:
                raw_element_counts[cls.STEM_MAP[s]] += 1.0

        # 地支カウント(動的距離対衝減衰考慮)
        clash_factors = cls._calculate_clash_factors(branches)
        for idx, b in enumerate(branches):
            if b in cls.BRANCH_MAP:
                target_el = cls.BRANCH_MAP[b]
                raw_element_counts[target_el] += 1.5 * clash_factors[idx]

        gogyo_scores = {el: 0.0 for el in cls.ELEMENTS}

        # 2. 天干スコア算出 (通根・季節補正)
        for s in stems:
            if s not in cls.STEM_MAP:
                continue
            s_el = cls.STEM_MAP[s]
            weight = 1.0

            tsukon_factor = 1.0
            for b in branches:
                if b not in cls.ZOKAN_DETAIL:
                    continue
                for z_idx, (z_stem, _) in enumerate(cls.ZOKAN_DETAIL[b]):
                    if cls.STEM_MAP.get(z_stem) == s_el:
                        tsukon_factor = max(tsukon_factor, 1.4 if z_idx == 0 else 1.2)

            weight *= tsukon_factor
            s_weight = cls.BASE_SEASON_WEIGHTS[s_el][season]
            if s_weight < 1.0 and raw_element_counts[s_el] >= 2.5:
                s_weight = 1.1

            gogyo_scores[s_el] += weight * s_weight

        # 3. 地支スコア算出 (全地支の元蔵干計算 + 動的距離対衝減衰)
        for i, p in enumerate(pillars):
            b = p.get("branch")
            if b not in cls.BRANCH_MAP:
                continue

            c_factor = clash_factors[i]
            base_branch_weight = 2.4 if p.get("name") == "月" else 1.2

            for z_stem, ratio in cls.ZOKAN_DETAIL.get(b, []):
                z_el = cls.STEM_MAP[z_stem]
                s_weight = cls.BASE_SEASON_WEIGHTS[z_el][season]
                if s_weight < 1.0 and raw_element_counts[z_el] >= 2.5:
                    s_weight = 1.1

                # 元蔵干のスコア計算 (動的距離対衝減衰を乗算)
                gogyo_scores[z_el] += (base_branch_weight * ratio * c_factor) * s_weight

        # 4. 合化ボーナススコアの加算 (ハイブリッド方式)
        goka_bonuses = cls._detect_goka_bonuses(branches, other_stems, month_branch)
        for el, bonus_val in goka_bonuses.items():
            if bonus_val > 0:
                s_weight = cls.BASE_SEASON_WEIGHTS[el][season]
                gogyo_scores[el] += bonus_val * s_weight

        # 5. 無根衰減処理 (相剋判定)
        for el in cls.ELEMENTS:
            attacking_el = [k for k, v in cls.KOKU_MAP.items() if v == el][0]
            if gogyo_scores[attacking_el] >= 2.5:
                has_root = any(
                    cls.STEM_MAP.get(z_stem) == el
                    for b in branches if b in cls.ZOKAN_DETAIL
                    for z_stem, _ in cls.ZOKAN_DETAIL[b]
                )
                if not has_root:
                    gogyo_scores[el] *= 0.4

        # --------------------------------------------------
        # 身強身弱判定ブロック
        # --------------------------------------------------
        day_el_idx = cls.ELEMENTS.index(day_stem_el)
        hibo_el = day_stem_el
        insei_el = cls.ELEMENTS[(day_el_idx - 1) % 5]

        month_el = cls.BRANCH_MAP[month_branch]
        is_tokurei = month_el == hibo_el or month_el == insei_el

        has_day_stem_root = any(
            cls.STEM_MAP.get(z_stem) == day_stem_el
            for b in branches if b in cls.ZOKAN_DETAIL
            for z_stem, _ in cls.ZOKAN_DETAIL[b]
        )

        insei_score = gogyo_scores[insei_el]
        hibo_score = gogyo_scores[hibo_el]

        is_inta_mijaku = False
        effective_insei_score = insei_score

        if not has_day_stem_root and insei_score >= 4.0 and insei_score > hibo_score * 2:
            is_inta_mijaku = True
            effective_insei_score = insei_score * 0.2

        jitou_score = hibo_score + effective_insei_score
        itau_score = sum(gogyo_scores.values()) - (hibo_score + insei_score)

        if is_inta_mijaku:
            judgment = "身弱（印多身弱）"
        elif is_tokurei and has_day_stem_root:
            judgment = "身強"
        elif not is_tokurei and not has_day_stem_root and jitou_score < itau_score * 1.2:
            judgment = "身弱"
        else:
            judgment = "身強" if jitou_score >= itau_score else "身弱"

        gogyo_balance_rounded = {k: round(v, 2) for k, v in gogyo_scores.items()}

        return {
            "gogyo_balance": gogyo_balance_rounded,
            "day_stem_element": day_stem_el,
            "jitou_score": round(jitou_score, 2),
            "itau_score": round(itau_score, 2),
            "judgment": judgment,
            "goka_bonuses": goka_bonuses,
        }