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


# 뜻 있는 날만 한 줄(11/8 정오님과 정리: 날짜·달을 매일 크게 보여 줄 이유는 약하다).
# 절기 당일 > 보름 > 초하루 순. 그 밖의 날은 아무것도 띄우지 않는다.
TERM_NOTE = {
    "소한": "한 해 중 가장 추운 무렵이 시작돼요.", "대한": "큰 추위라는 뜻의 겨울 마지막 절기예요.",
    "입춘": "봄이 시작되는 날, 사주에서는 이날부터 새해예요.", "우수": "눈이 비로 바뀌고 얼음이 녹기 시작해요.",
    "경칩": "겨울잠 자던 벌레가 깨어난다는 날이에요.", "춘분": "낮과 밤의 길이가 거의 같아지는 날이에요.",
    "청명": "하늘이 맑고 밝아진다는 봄날이에요.", "곡우": "봄비가 곡식을 깨운다는 봄의 마지막 절기예요.",
    "입하": "여름이 시작되는 날이에요.", "소만": "만물이 차오르기 시작한다는 날이에요.",
    "망종": "씨 뿌리고 보리 거두기 바쁜 때예요.", "하지": "낮이 가장 긴 날이에요.",
    "소서": "본격적인 더위가 시작되는 때예요.", "대서": "한 해 중 가장 더운 무렵이에요.",
    "입추": "가을이 시작되는 날이에요.", "처서": "더위가 물러간다는 날이에요.",
    "백로": "이슬이 하얗게 맺히기 시작하는 때예요.", "추분": "낮과 밤의 길이가 다시 같아지는 날이에요.",
    "한로": "찬 이슬이 맺히는 깊은 가을이에요.", "상강": "서리가 내리기 시작하는 가을의 마지막 절기예요.",
    "입동": "겨울이 시작되는 날이에요.", "소설": "첫눈이 내린다는 때예요.",
    "대설": "큰 눈이 온다는 때예요.", "동지": "밤이 가장 긴 날, 팥죽 먹는 날이에요.",
}
MOON_DAY_NOTE = {1: ("음력 초하루", "새 달이 시작되는 날이에요."), 15: ("음력 보름", "달이 가장 둥근 날이에요.")}


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
    if info.get("days_to_term") == 0 and info["next_term"] in TERM_NOTE:
        info["special"] = dict(name=info["next_term"], note=TERM_NOTE[info["next_term"]])
    elif day in MOON_DAY_NOTE:
        name, note = MOON_DAY_NOTE[day]
        info["special"] = dict(name=name, note=note)
    prev = lunar.getPrevJieQi()
    if prev is not None and TERM_KO.get(prev.getName()):
        info["prev_term"] = TERM_KO[prev.getName()]
    return info
