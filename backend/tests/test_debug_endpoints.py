"""공개 운영에서 엔진 디버그 주소가 닫혀 있는지 확인한다."""
from fastapi.testclient import TestClient

import main


def test_debug_engine_endpoint_is_closed_by_default(monkeypatch):
    monkeypatch.delenv("DALHA_ENABLE_DEBUG_ENDPOINTS", raising=False)
    response = TestClient(main.app).get("/api/test-saju-engine")
    assert response.status_code == 404


def test_debug_engine_endpoint_opens_only_with_explicit_flag(monkeypatch):
    monkeypatch.setenv("DALHA_ENABLE_DEBUG_ENDPOINTS", "1")
    response = TestClient(main.app).get("/api/test-saju-engine")
    assert response.status_code == 200
    assert "comparison" in response.json()
