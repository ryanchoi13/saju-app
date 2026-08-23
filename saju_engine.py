from korean_lunar_calendar import KoreanLunarCalendar

CHEONGAN = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
JIJI = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]

OHENG_MAP = {
    "갑": "목", "을": "목", "인": "목", "묘": "목",
    "병": "화", "정": "화", "사": "화", "오": "화",
    "무": "토", "기": "토", "진": "토", "술": "토", "축": "토", "미": "토",
    "경": "금", "신": "금", "유": "금",
    "임": "수", "계": "수", "해": "수", "자": "수"
}

def calculate_saju(year: int, month: int, day: int, sijin_index: int = None, is_unknown_time: bool = False):
    calendar = KoreanLunarCalendar()
    calendar.setSolarDate(year, month, day)
    
    gapja_str = calendar.getChineseGapJaString()
    hanja_to_hangul = {
        '甲':'갑', '乙':'을', '丙':'병', '丁':'정', '戊':'무', '己':'기', '庚':'경', '辛':'신', '壬':'임', '癸':'계',
        '子':'자', '丑':'축', '寅':'인', '卯':'묘', '辰':'진', '巳':'사', '午':'오', '未':'미', '申':'신', '酉':'유', '戌':'술', '亥':'해'
    }
    
    raw_pillars = gapja_str.split()
    year_p = "".join([hanja_to_hangul.get(c, c) for c in raw_pillars[0].replace("年", "")])
    month_p = "".join([hanja_to_hangul.get(c, c) for c in raw_pillars[1].replace("月", "")])
    day_p = "".join([hanja_to_hangul.get(c, c) for c in raw_pillars[2].replace("日", "")])

    day_gan = day_p[0]

    hour_p = None
    chars = [year_p[0], year_p[1], month_p[0], month_p[1], day_p[0], day_p[1]]

    if not is_unknown_time and sijin_index is not None and 0 <= sijin_index < 12:
        hour_ji = JIJI[sijin_index]
        hour_gan_idx = (CHEONGAN.index(day_gan) % 5 * 2 + sijin_index) % 10
        hour_gan = CHEONGAN[hour_gan_idx]
        hour_p = f"{hour_gan}{hour_ji}"
        chars.extend([hour_gan, hour_ji])

    total_count = len(chars)
    oheng_counts = {"목": 0, "화": 0, "토": 0, "금": 0, "수": 0}
    
    for c in chars:
        oheng = OHENG_MAP.get(c)
        if oheng:
            oheng_counts[oheng] += 1
            
    oheng_percent = {k: round((v / total_count) * 100, 1) for k, v in oheng_counts.items()}

    return {
        "pillars": {
            "year": year_p,
            "month": month_p,
            "day": day_p,
            "hour": hour_p
        },
        "is_unknown_time": is_unknown_time,
        "oheng_ratio": oheng_percent,
        "day_gan": day_gan
    }