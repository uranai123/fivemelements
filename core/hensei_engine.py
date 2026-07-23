# -*- coding: utf-8 -*-

class HenseiEngine:
    # 五行のインデックス (0:木, 1:火, 2:土, 3:金, 4:水)
    # 甲乙:木(0), 丙丁:火(1), 戊己:土(2), 庚辛:金(3), 壬癸:水(4)
    ELEMENT_MAP = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]

    # 通変星マップ (五行の差分: 0=同, 1=生, 2=剋(財), 3=剋(官), 4=洩)
    # 実際には「日干から見て」という相対関係で計算します
    @staticmethod
    def get_hensei(day_stem_idx: int, target_stem_idx: int):
        if day_stem_idx == target_stem_idx:
            return "比肩" # 厳密には同種だが、日干そのものは「－」で扱う想定

        day_elem = HenseiEngine.ELEMENT_MAP[day_stem_idx]
        target_elem = HenseiEngine.ELEMENT_MAP[target_stem_idx]
        
        # 陰陽が同じならTrue, 違うならFalse
        is_same_parity = (day_stem_idx % 2) == (target_stem_idx % 2)
        
        # 五行の相関計算 (day -> target)
        # 0:比肩/劫財, 1:食神/傷官, 2:偏財/正財, 3:偏官/正官, 4:偏印/印綬
        diff = (target_elem - day_elem) % 5
        
        if diff == 0:
            return "比肩" if is_same_parity else "劫財"
        elif diff == 1:
            return "食神" if is_same_parity else "傷官"
        elif diff == 2:
            return "偏財" if is_same_parity else "正財"
        elif diff == 3: # 官殺は剋される側（自分が剋する側が財）
            return "偏官" if is_same_parity else "正官"
        elif diff == 4: # 印は生じる側
            return "偏印" if is_same_parity else "印綬"
        
        return "不明"