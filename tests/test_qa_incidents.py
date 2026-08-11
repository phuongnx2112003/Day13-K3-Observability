from __future__ import annotations

from fastapi.testclient import TestClient

from app import incidents
from app.main import app
from app.mock_llm import FakeLLM
from app.mock_rag import retrieve


def teardown_function() -> None:
    for name in incidents.STATE:
        incidents.STATE[name] = False


def test_practice_incident_state_can_be_enabled_and_disabled() -> None:
    with TestClient(app) as client:
        enabled = client.post("/incidents/rag_slow/enable")
        assert enabled.status_code == 200
        assert enabled.json()["incidents"]["rag_slow"] is True

        disabled = client.post("/incidents/rag_slow/disable")
        assert disabled.status_code == 200
        assert disabled.json()["incidents"]["rag_slow"] is False


def test_unknown_practice_incident_is_rejected() -> None:
    with TestClient(app) as client:
        response = client.post("/incidents/not-a-real-incident/enable")

    assert response.status_code == 404


def test_rag_slow_incident_requests_slow_path(monkeypatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr("app.mock_rag.time.sleep", sleeps.append)
    incidents.enable("rag_slow")
    try:
        assert retrieve("Explain monitoring")
    finally:
        incidents.disable("rag_slow")
    assert sleeps == [2.5]


def test_tool_fail_incident_raises_retrieval_error() -> None:
    incidents.enable("tool_fail")
    try:
        try:
            retrieve("Explain monitoring")
        except RuntimeError as exc:
            assert str(exc) == "Vector store timeout"
        else:  # pragma: no cover - defensive assertion
            raise AssertionError("tool_fail must raise RuntimeError")
    finally:
        incidents.disable("tool_fail")


def test_cost_spike_incident_increases_output_tokens(monkeypatch) -> None:
    monkeypatch.setattr("app.mock_llm.random.randint", lambda _low, _high: 100)
    baseline = FakeLLM().generate("short prompt").usage.output_tokens
    incidents.enable("cost_spike")
    try:
        incident_tokens = FakeLLM().generate("short prompt").usage.output_tokens
    finally:
        incidents.disable("cost_spike")

    assert incident_tokens >= baseline * 4
