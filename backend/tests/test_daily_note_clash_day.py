"""홈 "오늘, 기억할 한 가지"(unified_advice) — 부딪히는 날 관계 처방은 등급 카드와 같은 '묵히기' 방향 (2026-11-02)."""
from app.engine.services import overall_narrative as on
from app.engine.services.daily_copy import find_flagged


def _selection(scope, domain):
    return {"scope": scope, "selected": [{"domain": domain, "label": domain, "mode": "change"}],
            "primary_domains": [domain]}


def test_daily_clash_day_love_note_defers_talk():
    out = on.render_overall(_selection("daily", "love"))
    assert out["unified_advice"] == on.DAILY_SPECIAL["love", "change"][5]
    assert "내일" in out["unified_advice"]
    assert "짐작했던 기대" not in out["unified_advice"]


def test_daily_clash_day_relationships_note_defers_argument():
    out = on.render_overall(_selection("daily", "relationships"))
    assert out["unified_advice"] == on.DAILY_SPECIAL["relationships", "change"][5]


def test_long_scopes_keep_dialogue_copy():
    # 올해·이번 달처럼 긴 범위는 "대화로 확인하기"를 그대로 쓴다.
    out = on.render_overall(_selection("annual", "love"))
    assert out["unified_advice"] == on.SPECIAL["love", "change"][5]


def test_daily_special_copy_is_clean():
    for key, texts in on.DAILY_SPECIAL.items():
        assert len(texts) == 6, key
        for text in texts:
            assert not find_flagged(text), (key, text)
            assert "수 있어요" not in text and "일지도" not in text, (key, text)
