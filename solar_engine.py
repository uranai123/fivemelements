# -*- coding: utf-8 -*-
from skyfield.api import load
from scipy.optimize import brentq
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta

class SolarEngine:
    def __init__(self):
        self.ts = load.timescale()
        self.eph = load('de421.bsp')
        self.earth = self.eph['earth']
        self.sun = self.eph['sun']

    def get_solar_longitude(self, t):
        astrometric = self.earth.at(t).observe(self.sun)
        _, lon, _ = astrometric.ecliptic_latlon(epoch=t)
        return lon.degrees

    def get_setsuiri(self, year: int, month_index: int):
        """
        指定した月(0-11)の節入り日時を計算する
        0: 立春, 1: 啓蟄, ..., 11: 小寒
        """
        # 目標とする黄経 (315度:立春)
        target_lon = (315 + (month_index * 30)) % 360
        
        # --- 修正: その月インデックスに対応する開始日を特定 ---
        # 0(立春)なら2月頃、11(小寒)なら翌1月頃を狙う
        # 節入りは毎月1回必ずあるので、その月の1日周辺から探索すれば十分
        # 2月(idx=0)を基準に、月数×30日を加算して開始日とする
        start_date = datetime(year, 1, 15) + timedelta(days=month_index * 30)
        
        # 探索範囲 (開始日から60日間)
        t_start = self.ts.utc(start_date.year, start_date.month, start_date.day)
        
        # 探索実行
        for day in range(60):
            t0 = t_start + day
            t1 = t_start + day + 1
            
            # 黄経差の計算
            def get_diff(t):
                lon = self.get_solar_longitude(t)
                return (lon - target_lon + 180) % 360 - 180

            diff0 = get_diff(t0)
            diff1 = get_diff(t1)
            
            # 符号が反転していれば、その区間に節入りが存在する
            if diff0 * diff1 <= 0:
                def func(jd):
                    return get_diff(self.ts.tt_jd(jd))
                
                try:
                    root_jd = brentq(func, t0.tt, t1.tt)
                    return self.ts.tt_jd(root_jd).utc_datetime()
                except ValueError:
                    continue
        return None

    def get_setsuiri_jst(self, year: int, month_index: int):
        utc_dt = self.get_setsuiri(year, month_index)
        if utc_dt is None:
            return None
        return utc_dt.astimezone(ZoneInfo("Asia/Tokyo"))

    def get_setsuiri_jst_by_month(self, year: int, month: int):
        """
        指定したカレンダー年と月(1〜12)に対応する節入りのJST日時を取得する
        （2月=立春(index 0) 〜 1月=小寒(index 11) のマッピング）
        """
        # カレンダー月(1〜12)を節入りインデックス(0〜11)に変換
        if month >= 2:
            month_index = month - 2
        else:
            month_index = 11  # 1月の場合は小寒（index 11）
            
        return self.get_setsuiri_jst(year, month_index)