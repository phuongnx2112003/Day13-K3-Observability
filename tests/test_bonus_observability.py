from __future__ import annotations

import json

from app import audit_logging, incidents
from app.mock_llm import FakeLLM, MAX_OUTPUT_TOKENS
from scripts.anomaly_check import analyze_records


def test_cost_spike_output_is_capped(monkeypatch) -> None:
    monkeypatch.setattr("app.mock_llm.random.randint", lambda _low, _high: 180)
    incidents.enable("cost_spike")
    try:
        response = FakeLLM().generate("test")
    finally:
        incidents.disable("cost_spike")

    assert response.usage.output_tokens == MAX_OUTPUT_TOKENS


def test_audit_log_is_separate_and_scrubs_pii(monkeypatch, tmp_path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    monkeypatch.setattr(audit_logging, "AUDIT_LOG_PATH", audit_path)

    audit_logging.write_audit_event("incident_enabled", note="email qa@example.com")

    record = json.loads(audit_path.read_text(encoding="utf-8"))
    assert record["event"] == "incident_enabled"
    assert "qa@example.com" not in json.dumps(record)
    assert "REDACTED_EMAIL" in json.dumps(record)


def test_anomaly_check_detects_pii_latency_and_error_rate() -> None:
    records = [
        {"event": "request_received", "payload": {"message_preview": "Call 090 123 4567"}},
        {"event": "request_received"},
        {"event": "request_failed"},
        {"event": "response_sent", "latency_ms": 3500},
    ]

    summary = analyze_records(records, latency_slo_ms=3000, error_slo_pct=2)

    assert {anomaly["type"] for anomaly in summary["anomalies"]} == {
        "pii_leak",
        "high_latency",
        "high_error_rate",
    }
