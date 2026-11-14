"""테마운 '이런 이야기를 읽어요' 목차 = 풀이 안 칸 번호·제목 (2026-11-14).

정오님 요청: 바깥 목차와 풀이 안의 01·02·03… 이 같은 번호·같은 제목으로 맞아야 한다.
- index.html 의 목차(theme-toc)
- 구매 후 풀이의 칸 제목(h2) 순서
- 구매 전 잠긴 목록(03부터)
세 곳이 어긋나면 이 테스트가 깨진다.
"""
import datetime
import re
import unittest
from pathlib import Path

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services import career_sections, health_sections, love_sections, study_sections, wealth_sections
from app.engine.services.career import build_lifetime_career_report
from app.engine.services.health import build_lifetime_health_report
from app.engine.services.love import build_lifetime_love_report
from app.engine.services.study import build_lifetime_study_report
from app.engine.services.wealth import build_lifetime_wealth_report

INDEX = Path(__file__).resolve().parents[2] / "index.html"
THEMES = {
    "business": (build_lifetime_career_report, career_sections),
    "love": (build_lifetime_love_report, love_sections),
    "wealth": (build_lifetime_wealth_report, wealth_sections),
    "study": (build_lifetime_study_report, study_sections),
    "health": (build_lifetime_health_report, health_sections),
}
PEOPLE = [
    ("male", datetime.date(1978, 3, 13), datetime.time(10, 30)),
    ("female", datetime.date(1995, 7, 2), datetime.time(4, 10)),
    ("female", datetime.date(1988, 12, 24), datetime.time(22, 0)),
]


def _open_titles(html: str) -> list[str]:
    return re.findall(r'<section(?![^>]*data-locked)[^>]*>\s*<h2>(.*?)</h2>', html)


def _index_toc(key: str) -> list[tuple[str, str]]:
    page = INDEX.read_text(encoding="utf-8")
    block = re.search(r'<section id="concern-' + key + r'".*?<ol class="theme-toc">(.*?)</ol>', page, re.S)
    assert block, key
    return re.findall(r'<span class="toc-num">(\d+)</span><strong>(.*?)</strong>', block.group(1))


class ThemeTocMatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cores = [calculate_myeongri_core(BirthInput(name="t", gender=g, birth_date=d, birth_time=t),
                                             target_date=datetime.date(2026, 11, 14)) for g, d, t in PEOPLE]

    def test_index_toc_matches_paid_reading(self):
        for key, (build, _) in THEMES.items():
            toc = _index_toc(key)
            self.assertEqual([n for n, _ in toc], [f"{i:02d}" for i in range(1, len(toc) + 1)], key)
            for core in self.cores:
                titles = _open_titles(build(core, "t", is_unlocked=True)["content"])
                self.assertEqual([t for _, t in toc], titles, key)

    def test_locked_list_continues_same_numbers(self):
        for key, (build, sec) in THEMES.items():
            toc = _index_toc(key)
            html = build(self.cores[0], "t")["content"]
            free = _open_titles(html)
            self.assertEqual([t for _, t in toc[:len(free)]], free, key)
            locked = [(f"{i:02d}", t) for i, (_, t) in enumerate(sec.LOCKED_SECTIONS, len(free) + 1)]
            self.assertEqual(toc[len(free):], locked, key)
            shown = re.findall(r'<span class="locked-num">(\d+)</span> (.*?)</li>', html)
            self.assertEqual(shown, locked, key)


if __name__ == "__main__":
    unittest.main()
