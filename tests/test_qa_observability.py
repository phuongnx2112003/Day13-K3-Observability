from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi.testclient import TestClient

from app import logging_config
from app.main import app


def _chat_payload(message: str = "Explain observability") -> dict[str, str]:
    return {
        "user_id": "qa-user-01",
        "session_id": "qa-session-01",
        "feature": "monitoring",
        "message": message,
    }


def _events(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_request_id_is_preserved_and_returned_in_response(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(logging_config, "LOG_PATH", tmp_path / "logs.jsonl")
    supplied_id = "req-a1b2c3d4"

    with TestClient(app) as client:
        response = client.post(
            "/chat", headers={"x-request-id": supplied_id}, json=_chat_payload()
        )

    assert response.status_code == 200
    assert response.headers["x-request-id"] == supplied_id
    assert response.json()["correlation_id"] == supplied_id
    request_events = [
        event for event in _events(tmp_path / "logs.jsonl") if "correlation_id" in event
    ]
    assert {event["correlation_id"] for event in request_events} == {supplied_id}


def test_missing_request_id_is_generated_and_not_reused(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(logging_config, "LOG_PATH", tmp_path / "logs.jsonl")

    with TestClient(app) as client:
        first = client.post("/chat", json=_chat_payload())
        second = client.post("/chat", json=_chat_payload())

    first_id = first.headers["x-request-id"]
    second_id = second.headers["x-request-id"]
    assert re.fullmatch(r"req-[0-9a-f]{8}", first_id)
    assert re.fullmatch(r"req-[0-9a-f]{8}", second_id)
    assert first_id != second_id


def test_log_context_is_enriched_and_pii_is_redacted(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(logging_config, "LOG_PATH", tmp_path / "logs.jsonl")
    message = "Contact qa.user@example.com or 090 123 4567"

    with TestClient(app) as client:
        response = client.post("/chat", json=_chat_payload(message))

    assert response.status_code == 200
    events = _events(tmp_path / "logs.jsonl")
    request_event = next(event for event in events if event["event"] == "request_received")
    for field in ("correlation_id", "user_id_hash", "session_id", "feature", "model", "env"):
        assert request_event.get(field)
    serialized = json.dumps(events, ensure_ascii=False)
    assert "qa.user@example.com" not in serialized
    assert "090 123 4567" not in serialized
    assert "REDACTED_EMAIL" in serialized
    assert "REDACTED_PHONE_VN" in serialized
