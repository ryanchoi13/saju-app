"""옛 엔진 비교용 디버그 주소는 삭제됐다. 환경변수를 켜도 다시 열리지 않아야 한다."""
from fastapi.testclient import TestClient

import main


def test_debug_engine_endpoint_is_gone(monkeypatch):
    monkeypatch.setenv("DALHA_ENABLE_DEBUG_ENDPOINTS", "1")
    assert TestClient(main.app).get("/api/test-saju-engine").status_code == 404
