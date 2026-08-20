# -*- coding: utf-8 -*-
from datetime import datetime
from zoneinfo import ZoneInfo
from scipy.optimize import brentq
from skyfield.api import load

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

    def get_setsuiri_by_month(self, year: int, month: int):
        """
        指定した西暦年(year)・月(month: 1-12)に存在する「節入り」日時(UTC)を返す
        1月: 小寒(285°), 2月: 立春(315°), ..., 12月: 大雪(255°)
        """
        # 1月=小寒(285度)、2月=立春(315度) ... 12月=大雪(255度)
        target_lon = (285 + (month - 1) * 30) % 360
        
        # 該当月の1日から探索を開始
        start_date = datetime(year, month, 1)
        t_start = self.ts.utc(start_date.year, start_date.month, start_date.day)
        
        # 1ヶ月間(35日)探索すれば必ず対象月内の節入りを発見できる
        for day in range(35):
            t0 = t_start + day
            t1 = t_start + day + 1
            
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

    def get_setsuiri_jst_by_month(self, year: int, month: int):
        """
        指定した西暦年(year)・月(month: 1-12)の節入り日時(JST)を返す
        """
        utc_dt = self.get_setsuiri_by_month(year, month)
        if utc_dt is None:
            return None
        return utc_dt.astimezone(ZoneInfo("Asia/Tokyo"))

    # --- 従来インターフェースとの互換用メソッド ---
    def get_setsuiri(self, year: int, month_index: int):
        """
        旧インターフェース互換 (month_index 0:立春 ... 11:小寒)
        ※ 11(小寒)の場合は指定年の翌年1月の小寒を取得します
        """
        if month_index == 11:
            return self.get_setsuiri_by_month(year + 1, 1)
        else:
            return self.get_setsuiri_by_month(year, month_index + 2)

    def get_setsuiri_jst(self, year: int, month_index: int):
        utc_dt = self.get_setsuiri(year, month_index)
        if utc_dt is None:
            return None
        return utc_dt.astimezone(ZoneInfo("Asia/Tokyo"))