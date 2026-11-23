"""전날과 같은 칸의 오행이 같을 때 붙는 연결 문구(2026-11-20)."""
from fashion_v2.daily_colors import CONTINUATION_TEMPLATES, continuation_caption

PREV = dict(element_a="金", element_b="土")


def test_no_caption_without_previous_day_or_overlap():
    assert continuation_caption(None, dict(element_a="金", element_b="土"), 1) == ""
    assert continuation_caption(PREV, dict(element_a="水", element_b="火"), 1) == ""
    # 칸이 서로 바뀐 겹침(어제 1칸 金 → 오늘 2칸 金)은 이어짐으로 보지 않는다
    assert continuation_caption(PREV, dict(element_a="土", element_b="金"), 1) == ""


def test_names_the_shared_elements_in_slot_order():
    one = continuation_caption(PREV, dict(element_a="金", element_b="火"), 0)
    assert "금(金)" in one and "토(土)" not in one
    both = continuation_caption(PREV, dict(element_a="金", element_b="土"), 0)
    assert "금(金)·토(土)" in both


def test_templates_alternate_day_by_day_and_all_used():
    today = dict(element_a="金", element_b="火")
    texts = [continuation_caption(PREV, today, n) for n in range(730000, 730400)]
    assert all(texts[i] != texts[i + 1] for i in range(len(texts) - 1))   # 이틀 연속 같은 문장 없음
    from collections import Counter
    assert max(Counter(texts).values()) - min(Counter(texts).values()) <= 4   # 쏠리지 않음
    assert len(set(texts)) == len(CONTINUATION_TEMPLATES) == 4
