"""화면(index.html)이 아는 풀이 버전과 서버가 새로 쓰는 버전이 같은지 검사.

다르면 '구매한 풀이 새로 받기'를 눌러도 버튼이 계속 남는다(2026-10-21 애정운에서 발견).
"""
import pathlib
import re
import unittest

from app.engine.services.annual_editorial import NARRATIVE_VERSION as ANNUAL
from app.engine.services.career import CAREER_NARRATIVE_VERSION
from app.engine.services.health import HEALTH_NARRATIVE_VERSION
from app.engine.services.lifetime import LIFETIME_NARRATIVE_VERSION
from app.engine.services.love import LOVE_NARRATIVE_VERSION
from app.engine.services.reading_editorial import THEME_VERSION

HTML = (pathlib.Path(__file__).resolve().parents[2] / "index.html").read_text(encoding="utf-8")


def _const(name):
    return re.search(rf"const {name} = '([^']+)';", HTML).group(1)


class ReportVersionSyncTests(unittest.TestCase):
    def test_shared_constants(self):
        self.assertEqual(_const("ANNUAL_NARRATIVE_VERSION"), ANNUAL)
        self.assertEqual(_const("LIFETIME_NARRATIVE_VERSION"), LIFETIME_NARRATIVE_VERSION)
        self.assertEqual(_const("THEME_NARRATIVE_VERSION"), THEME_VERSION)

    def test_theme_report_versions(self):
        block = re.search(r"const REPORT_NARRATIVE_VERSION = \{(.*?)\};", HTML, re.S).group(1)
        found = dict(re.findall(r"(\w+): '([^']+)'", block))
        self.assertEqual(found, {"business": CAREER_NARRATIVE_VERSION,
                                 "love": LOVE_NARRATIVE_VERSION,
                                 "health": HEALTH_NARRATIVE_VERSION})


if __name__ == "__main__":
    unittest.main()
