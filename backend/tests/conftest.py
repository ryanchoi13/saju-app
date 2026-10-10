"""CI 기준선 격리.

known_failures.txt 에 적힌 테스트는 main 에서 이미 실패하던 것들이라, 새 문제를 가리지 않도록 실행에서 제외한다.
- 제외된 개수는 매번 터미널 요약에 출력된다(숨기지 않는다).
- 로컬에서 포함해 돌리려면 DALHA_RUN_KNOWN_FAILURES=1 을 설정한다.
- 목록의 테스트를 고쳤다면 known_failures.txt 에서 지운다.
"""
import os
from pathlib import Path

_KNOWN = Path(__file__).with_name("known_failures.txt")
_deselected_count = 0


def _load():
    if os.environ.get("DALHA_RUN_KNOWN_FAILURES") == "1" or not _KNOWN.exists():
        return set()
    lines = (ln.strip() for ln in _KNOWN.read_text(encoding="utf-8").splitlines())
    return {ln for ln in lines if ln and not ln.startswith("#")}


def pytest_collection_modifyitems(config, items):
    global _deselected_count
    known = _load()
    if not known:
        return
    keep, dropped = [], []
    for item in items:
        (dropped if item.nodeid in known else keep).append(item)
    if dropped:
        config.hook.pytest_deselected(items=dropped)
        items[:] = keep
        _deselected_count = len(dropped)


def pytest_terminal_summary(terminalreporter):
    if _deselected_count:
        terminalreporter.write_line(
            f"[known_failures] {_deselected_count}개 테스트를 기준선 격리로 건너뜀 "
            f"(backend/tests/known_failures.txt) — 고친 항목은 목록에서 지워 주세요.",
            yellow=True)
