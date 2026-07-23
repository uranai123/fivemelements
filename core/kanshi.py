# -*- coding: utf-8 -*-
import datetime

class KanshiEngine:
    TENKAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    CHISHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

    # 夜子時対応テーブル (0:甲己, 1:乙庚, 2:丙辛, 3:丁壬, 4:戊癸)
    HOURLY_TABLE = [
        ["甲子", "丙子", "戊子", "庚子", "壬子"], # 0-1
        ["乙丑", "丁丑", "己丑", "辛丑", "癸丑"], # 1-3
        ["丙寅", "戊寅", "庚寅", "壬寅", "甲寅"], # 3-5
        ["丁卯", "己卯", "辛卯", "癸卯", "乙卯"], # 5-7
        ["戊辰", "庚辰", "壬辰", "甲辰", "丙辰"], # 7-9
        ["己巳", "辛巳", "癸巳", "乙巳", "丁巳"], # 9-11
        ["庚午", "壬午", "甲午", "丙午", "戊午"], # 11-13
        ["辛未", "癸未", "乙未", "丁未", "己未"], # 13-15
        ["壬申", "甲申", "丙申", "戊申", "庚申"], # 15-17
        ["癸酉", "乙酉", "丁酉", "己酉", "辛酉"], # 17-19
        ["甲戌", "丙戌", "戊戌", "庚戌", "壬戌"], # 19-21
        ["乙亥", "丁亥", "己亥", "辛亥", "癸亥"], # 21-23
        ["丙子", "戊子", "庚子", "壬子", "甲子"]  # 23-0 (夜子時)
    ]

    @staticmethod
    def get_hour_kanshi(day_tenkan_idx: int, hour: int):
        """提示されたテーブルに基づき時柱を算出"""
        if 0 <= hour < 1: row = 0
        elif 23 <= hour < 24: row = 12
        else: row = (hour + 1) // 2
        
        col = day_tenkan_idx % 5
        kanshi_str = KanshiEngine.HOURLY_TABLE[row][col]
        return (KanshiEngine.TENKAN.index(kanshi_str[0]), KanshiEngine.CHISHI.index(kanshi_str[1]))

    @staticmethod
    def get_year_kanshi(year: int):
        """年柱の算出: 1984年が甲子"""
        stem_idx = (year - 4) % 10
        branch_idx = (year - 4) % 12
        return stem_idx, branch_idx

    @staticmethod
    def get_month_kanshi(year_stem_idx: int, month_idx: int):
        """
        月柱の算出: 五虎遁の法
        year_stem_idx: 年干のインデックス (甲=0, ... 丁=3)
        month_idx: 節入り月からの相対インデックス (寅=0, 卯=1, ..., 子=10)
        """
        # 年干に対応する「寅月（月インデックス0）」の天干インデックス
        # 甲(0)/己(5) -> 丙(2)
        # 乙(1)/庚(6) -> 戊(4)
        # 丙(2)/辛(7) -> 庚(6)
        # 丁(3)/壬(8) -> 壬(8)
        # 戊(4)/癸(9) -> 甲(0)
        start_stems = [2, 4, 6, 8, 0]
        
        # 年干を5で割った余りで寅月の天干を取得
        base_stem_idx = start_stems[year_stem_idx % 5]
        
        # 寅(0)から数えてmonth_idx分進める
        stem_idx = (base_stem_idx + month_idx) % 10
        branch_idx = (2 + month_idx) % 12  # 寅(2)からスタート
        
        return stem_idx, branch_idx

    @staticmethod
    def get_day_kanshi(target_date: datetime.datetime):
        """日柱の算出: 基準日 1900/1/1 は甲戌"""
        base_date = datetime.datetime(1900, 1, 1)
        # タイムゾーンがあれば除去
        if target_date.tzinfo is not None:
            target_date = target_date.replace(tzinfo=None)
        
        delta = (target_date - base_date).days
        # 甲戌はインデックス (0, 10)
        stem_idx = (0 + delta) % 10 # 基準が0(甲)のため deltaをそのまま足す
        branch_idx = (10 + delta) % 12
        return stem_idx, branch_idx

# --- テスト実行 ---
if __name__ == "__main__":
    target = datetime.datetime(2026, 3, 15, 0, 30)
    
    # 動作確認
    y_ten, y_chi = KanshiEngine.get_year_kanshi(target.year)
    m_ten, m_chi = KanshiEngine.get_month_kanshi(y_ten, 1) # 2月(卯月)を例として
    d_ten, d_chi = KanshiEngine.get_day_kanshi(target)
    h_ten, h_chi = KanshiEngine.get_hour_kanshi(d_ten, target.hour)
    
    print(f"日付: {target}")
    print(f"年柱: {KanshiEngine.TENKAN[y_ten]}{KanshiEngine.CHISHI[y_chi]}")
    print(f"月柱: {KanshiEngine.TENKAN[m_ten]}{KanshiEngine.CHISHI[m_chi]}")
    print(f"日柱: {KanshiEngine.TENKAN[d_ten]}{KanshiEngine.CHISHI[d_chi]}")
    print(f"時柱: {KanshiEngine.TENKAN[h_ten]}{KanshiEngine.CHISHI[h_chi]}")