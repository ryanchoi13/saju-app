"""오늘의 음력·달 모양·다음 절기 (2026-11-08 A안 '일력' 홈 머리).

홈 맨 위 날짜 옆에 그날의 실제 달 모양을 그린다. 음력 날짜가 곧 달의 나이라서
화면은 lunar_day 하나로 달 모양을 계산한다(아래 phase_name 과 같은 구간).
"""
from __future__ import annotations

from datetime import date

from lunar_python import Solar

TERM_KO = {
    "小寒": "소한", "大寒": "대한", "立春": "입춘", "雨水": "우수", "惊蛰": "경칩", "驚蟄": "경칩",
    "春分": "춘분", "清明": "청명", "谷雨": "곡우", "穀雨": "곡우", "立夏": "입하", "小满": "소만",
    "小滿": "소만", "芒种": "망종", "芒種": "망종", "夏至": "하지", "小暑": "소서", "大暑": "대서",
    "立秋": "입추", "处暑": "처서", "處暑": "처서", "白露": "백로", "秋分": "추분", "寒露": "한로",
    "霜降": "상강", "立冬": "입동", "小雪": "소설", "大雪": "대설", "冬至": "동지",
    "DONG_ZHI": "동지", "XIAO_HAN": "소한", "DA_HAN": "대한", "LI_CHUN": "입춘", "YU_SHUI": "우수",
    "JING_ZHE": "경칩", "DA_XUE": "대설",
}

# 음력 날짜(달의 나이) → 달 이름. 한국어에서 흔히 쓰는 이름만.
_PHASES = ((1, "초하루"), (2, "초승달"), (6, "상현달"), (10, "차오르는 달"), (14, "보름달"),
           (17, "기우는 달"), (21, "하현달"), (25, "그믐달"), (29, "그믐"))


def phase_name(lunar_day: int) -> str:
    name = _PHASES[0][1]
    for start, label in _PHASES:
        if lunar_day >= start:
            name = label
    return name


def lunar_info(target: date) -> dict:
    lunar = Solar.fromYmd(target.year, target.month, target.day).getLunar()
    month = lunar.getMonth()
    day = lunar.getDay()
    info = dict(month=abs(month), day=day, leap=month < 0, phase=phase_name(day))
    nxt = lunar.getNextJieQi()
    if nxt is not None:
        s = nxt.getSolar()
        days = (date(s.getYear(), s.getMonth(), s.getDay()) - target).days
        name = TERM_KO.get(nxt.getName())
        if name and days >= 0:
            info.update(next_term=name, days_to_term=days)
    prev = lunar.getPrevJieQi()
    if prev is not None and TERM_KO.get(prev.getName()):
        info["prev_term"] = TERM_KO[prev.getName()]
    return info
