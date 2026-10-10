"""사용자 화면에 나가는 문구 은행에 금지 어휘(인사고과식 HR 표현)가 들어가지 않게 막는다.

기준은 annual_copy.find_banned 하나다. 여러 문구 파일의 주석이 "테스트가 전수 검사한다"고 적어 두었지만
실제로 이를 검사하는 테스트가 없어서 금지어가 섞여 들어갔다(2026-10-10 정리). 이 테스트가 그 약속을 지킨다.

검사 대상: 엔진 services 아래 모든 .py, 루트의 tarot_catalog.py·zodiac_daily.py 의 문자열 상수.
제외: 모듈·함수·클래스 설명문(docstring), 금지어 목록 정의(_BANNED_SOURCES) 자체.
"""
import ast
import unittest
from pathlib import Path

from app.engine.services.annual_copy import find_banned

ROOT = Path(__file__).resolve().parents[2]
SERVICES = ROOT / "backend" / "app" / "engine" / "services"
EXTRA = [ROOT / "tarot_catalog.py", ROOT / "zodiac_daily.py"]


def _docstring_ids(tree):
    ids = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                ids.add(id(body[0].value))
    return ids


def _banned_definition_ids(tree):
    ids = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "_BANNED_SOURCES" for t in node.targets
        ):
            ids.update(id(n) for n in ast.walk(node))
    return ids


def _hits(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    skip = _docstring_ids(tree) | _banned_definition_ids(tree)
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in skip:
            words = find_banned(node.value)
            if words:
                found.append(f"{path.name}:{node.lineno} {words} {node.value[:40]!r}")
    return found


class BannedVocabularyTests(unittest.TestCase):
    def test_copy_banks_have_no_banned_vocabulary(self):
        files = sorted(SERVICES.glob("*.py")) + EXTRA
        self.assertTrue(files, "검사할 파일을 찾지 못했습니다")
        found = []
        for path in files:
            found.extend(_hits(path))
        self.assertEqual(found, [], "금지 어휘가 문구에 들어 있습니다:\n" + "\n".join(found))

    def test_detector_still_catches_the_known_words(self):
        # 금지어 목록이 실수로 비워지면 위 검사가 조용히 통과하므로 감지기 자체도 확인한다.
        for text in ("성과를 설명하세요", "정산 날짜", "각자의 몫", "손실 한도", "작업 시간을 줄였다", "KPI"):
            self.assertTrue(find_banned(text), text)
        self.assertEqual(find_banned("현실적인 선택과 완성도"), [])


if __name__ == "__main__":
    unittest.main()
