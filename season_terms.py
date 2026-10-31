"""24절기: 지금 절기와 다음 절기(한국 시간 기준). 홈의 '지금은 ○○' 카드용.

절기 시각은 lunar_python(만세력과 같은 라이브러리)에서 가져온다.
문구는 운세가 아니라 그 철의 모습 한 줄 — 짧고 쉬운 말로.
"""
from datetime import date, datetime, timedelta, timezone

from lunar_python import Solar

KST = timezone(timedelta(hours=9))

# (한자 이름, 한글, 파일 번호·이름, 한 줄)
TERMS = [
    ("立春", "입춘", "01-ipchun", "봄이 시작되는 날이에요. 아직 춥지만 해가 조금씩 길어져요."),
    ("雨水", "우수", "02-usu", "눈이 비로 바뀌고 얼었던 땅이 풀리기 시작해요."),
    ("驚蟄", "경칩", "03-gyeongchip", "겨울잠 자던 개구리가 깨어난다는 때예요."),
    ("春分", "춘분", "04-chunbun", "낮과 밤의 길이가 같아져요. 이제부터 낮이 길어져요."),
    ("清明", "청명", "05-cheongmyeong", "하늘이 맑아지고 나무에 물이 오르는 때예요."),
    ("穀雨", "곡우", "06-gogu", "곡식을 깨우는 봄비가 내려요. 농사가 시작돼요."),
    ("立夏", "입하", "07-ipha", "여름이 시작돼요. 잎이 짙어지고 딸기가 익어요."),
    ("小滿", "소만", "08-soman", "햇볕이 넉넉해져 보리가 누렇게 익어 가요."),
    ("芒種", "망종", "09-mangjong", "보리를 거두고 모를 심는, 한 해 중 가장 바쁜 때예요."),
    ("夏至", "하지", "10-haji", "낮이 가장 긴 날이에요. 햇감자가 나와요."),
    ("小暑", "소서", "11-soseo", "본격적인 더위가 시작되고 장마가 이어져요."),
    ("大暑", "대서", "12-daeseo", "한 해 중 가장 더운 때예요. 시원한 그늘이 반가워요."),
    ("立秋", "입추", "13-ipchu", "가을이 시작돼요. 아직 덥지만 바람이 달라져요."),
    ("處暑", "처서", "14-cheoseo", "더위가 한풀 꺾이고 아침저녁이 선선해져요."),
    ("白露", "백로", "15-baengno", "풀잎에 이슬이 맺히기 시작해요. 가을이 깊어져요."),
    ("秋分", "추분", "16-chubun", "낮과 밤의 길이가 같아져요. 이제부터 밤이 길어져요."),
    ("寒露", "한로", "17-hallo", "찬 이슬이 내리고 단풍이 들기 시작해요."),
    ("霜降", "상강", "18-sanggang", "서리가 내리기 시작해요. 아침저녁 기온 차가 커져요."),
    ("立冬", "입동", "19-ipdong", "겨울이 시작돼요. 김장을 준비하는 때예요."),
    ("小雪", "소설", "20-soseol", "첫눈이 내리기 시작하는 때예요."),
    ("大雪", "대설", "21-daeseol", "눈이 많이 내리는 때예요. 본격적인 겨울이에요."),
    ("冬至", "동지", "22-dongji", "밤이 가장 긴 날이에요. 팥죽을 먹는 날이죠."),
    ("小寒", "소한", "23-sohan", "본격적인 추위가 시작돼요. 한 해 중 가장 추울 때가 많아요."),
    ("大寒", "대한", "24-daehan", "겨울의 마지막 절기예요. 이제 봄을 기다려요."),
]
_BY_HANJA = {t[0]: t for t in TERMS}
# lunar_python 은 일부 이름을 다른 글자로 돌려준다(간체·이체자).
_ALIAS = {"惊蛰": "驚蟄", "谷雨": "穀雨", "小满": "小滿", "芒种": "芒種", "处暑": "處暑",
          "白露": "白露", "寒露": "寒露", "清明": "清明", "大雪": "大雪", "小雪": "小雪"}


def _term(name):
    t = _BY_HANJA.get(_ALIAS.get(name, name))
    if t is None:
        raise KeyError(name)
    return t


def _kst_date(solar):
    return date(solar.getYear(), solar.getMonth(), solar.getDay())


def season_now(today=None):
    today = today or datetime.now(KST).date()
    lunar = Solar.fromYmd(today.year, today.month, today.day).getLunar()
    prev = lunar.getPrevJieQi(True)   # 오늘 포함
    nxt = lunar.getNextJieQi(False)   # 오늘 제외
    cur, nx = _term(prev.getName()), _term(nxt.getName())
    start, next_date = _kst_date(prev.getSolar()), _kst_date(nxt.getSolar())
    return {
        "name": cur[1], "hanja": cur[0], "art": f"/assets/season/jeolgi/{cur[2]}.webp", "line": cur[3],
        "start": start.isoformat(), "is_today": start == today,
        "next_name": nx[1], "next_date": next_date.isoformat(), "days_to_next": (next_date - today).days,
    }
