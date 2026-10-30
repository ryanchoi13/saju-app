"""코디 색을 정하는 단 하나의 함수(2026-10-30 틀).

아직 화면에 연결하지 않는다(화면은 '오늘의 행운 색' 두 개만). 코디 지식서가 쌓이면
rules.json 에 근거 있는 규칙을 더하고, 자동 검사(scripts/color_plan_report.py)가 기준을 넘으면 연결한다.
"""
from fashion_v2.color_plan.planner import plan_outfit_colors, tone_class, load_rules  # noqa: F401
