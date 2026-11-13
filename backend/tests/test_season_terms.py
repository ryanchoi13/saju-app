from datetime import date, timedelta
from pathlib import Path

import season_terms

ROOT = Path(__file__).resolve().parents[2]


def test_every_term_appears_once_a_year_with_art():
    seen = {}
    d = date(2026, 1, 1)
    while d < date(2027, 1, 1):
        s = season_terms.season_now(d)
        seen.setdefault(s["name"], s["art"])
        d += timedelta(days=1)
    assert len(seen) == 24
    for art in seen.values():
        assert (ROOT / art.lstrip("/")).exists(), art


def test_term_day_and_next():
    s = season_terms.season_now(date(2026, 10, 31))
    assert (s["name"], s["next_name"], s["next_date"], s["days_to_next"]) == ("상강", "입동", "2026-11-07", 7)
    assert season_terms.season_now(date(2026, 11, 7))["is_today"] is True


def test_order_and_hanja_for_the_label():
    s = season_terms.season_now(date(2026, 11, 13))
    assert (s["name"], s["hanja"], s["order"], s["order_label"]) == ("입동", "立冬", 19, "열아홉 번째")
    assert (s["next_name"], s["next_hanja"], s["next_date"]) == ("소설", "小雪", "2026-11-22")
    labels = set()
    d = date(2026, 1, 1)
    while d < date(2027, 1, 1):
        s = season_terms.season_now(d)
        assert 1 <= s["order"] <= 24 and s["hanja"] and s["next_hanja"]
        labels.add((s["order"], s["order_label"]))
        d += timedelta(days=1)
    assert len(labels) == 24
    assert dict(labels)[1] == "첫 번째" and dict(labels)[20] == "스무 번째" and dict(labels)[24] == "스물네 번째"
