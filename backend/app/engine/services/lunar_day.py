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


# 오늘의 달 한 줄(11/8 정오님: 큰 날짜 옆 달만 두지 말고 무슨 달인지 설명).
# 앞 문장 = 하늘에서 실제로 보이는 모습(천문 사실), 뒤 문장 = 생활에 옮긴 가벼운 권유(예언 아님).
PHASE_TITLE = {"초하루": "오늘은 음력 초하루", "보름달": "오늘은 보름달이 뜨는 날", "그믐": "오늘은 음력 그믐"}
PHASE_NOTE = {
    "초하루": "달이 새로 시작되는 날이라 밤하늘에 달이 보이지 않아요. 새 달에 해 볼 일 하나를 정해 두기 좋은 날이에요.",
    "초승달": "해가 진 뒤 서쪽 하늘에 가는 달이 잠깐 떠요. 시작한 일을 조금씩 키워 가는 때예요.",
    "상현달": "오른쪽 반이 밝은 반달이 저녁 하늘에 떠요. 한 달의 절반쯤 왔으니 속도를 한번 점검해 보세요.",
    "차오르는 달": "보름을 향해 하루하루 차오르는 달이에요. 벌여 둔 일에 힘을 더 싣기 좋은 때예요.",
    "보름달": "해가 지면 둥근 달이 떠서 밤새 하늘에 있어요. 한 달 중 가장 밝은 때라 해 온 일을 돌아보기 좋아요.",
    "기우는 달": "보름을 지나 조금씩 이우는 달이에요. 넘치게 벌인 것을 덜어 내기 좋은 때예요.",
    "하현달": "왼쪽 반이 밝은 반달이 자정 무렵 떠올라 아침까지 있어요. 남은 일을 정리하는 쪽으로 무게를 옮겨 보세요.",
    "그믐달": "새벽 동쪽 하늘에 눈썹 같은 달이 잠깐 떠요. 한 달을 마무리할 준비를 하는 때예요.",
    "그믐": "달이 해와 거의 겹쳐 하늘에서 보이지 않아요. 한 달을 마무리하고 비워 두기 좋은 날이에요.",
}


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
    phase = phase_name(day)
    info = dict(month=abs(month), day=day, leap=month < 0, phase=phase,
                phase_title=PHASE_TITLE.get(phase, f"오늘은 {phase}이 뜨는 날"), phase_note=PHASE_NOTE[phase])
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
