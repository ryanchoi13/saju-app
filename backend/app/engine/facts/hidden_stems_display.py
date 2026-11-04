"""화면에 보여 줄 지장간 순서 (2026-11-04 정오님 결정: 국내 만세력 방식).

여기(餘氣) → 중기(中氣) → 정기(正氣) 순서로, 여기도 빠짐없이 적는다.
중기가 없는 지지(子·卯·酉)는 가운데를 None 으로 비워 정기가 늘 마지막 줄에 오게 한다.

화면 표시 전용이다. 계산(오행 비중·통근·십성)은 hidden_stems.py 표를 그대로 쓴다.
"""

from __future__ import annotations

# (여기, 중기, 정기)
DISPLAY_HIDDEN_STEMS: dict[str, tuple[str | None, str | None, str]] = {
    "子": ("壬", None, "癸"),
    "丑": ("癸", "辛", "己"),
    "寅": ("戊", "丙", "甲"),
    "卯": ("甲", None, "乙"),
    "辰": ("乙", "癸", "戊"),
    "巳": ("戊", "庚", "丙"),
    "午": ("丙", "己", "丁"),
    "未": ("丁", "乙", "己"),
    "申": ("戊", "壬", "庚"),
    "酉": ("庚", None, "辛"),
    "戌": ("辛", "丁", "戊"),
    "亥": ("戊", "甲", "壬"),
}


def display_hidden_stems(branch: str) -> list[dict]:
    """[{"stem": "丙"|None, "main": bool}, ...] 위에서 아래(왼쪽에서 오른쪽) 순서."""
    residual, middle, main = DISPLAY_HIDDEN_STEMS[branch]
    return [
        {"stem": residual, "main": False},
        {"stem": middle, "main": False},
        {"stem": main, "main": True},
    ]
