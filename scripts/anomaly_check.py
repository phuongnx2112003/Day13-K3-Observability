from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

DEFAULT_LOG_PATH = Path("data/logs.jsonl")
DEFAULT_SLO_PATH = Path("config/slo.yaml")
PII_DETECTORS = {
    "email": re.compile(r"[\w.-]+@[\w.-]+\.\w+"),
    "phone_vn": re.compile(r"(?<!\d)(?:\+84|0)(?:[ .-]?\d){9}(?!\d)"),
    "credit_card": re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"),
}


def percentile(values: list[float], percent: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, round(percent / 100 * len(ordered) + 0.5) - 1))
    return ordered[index]


def load_records(log_path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            records.append(record)
    return records


def analyze_records(records: list[dict[str, Any]], latency_slo_ms: float, error_slo_pct: float) -> dict[str, Any]:
    response_events = [record for record in records if record.get("event") == "response_sent"]
    request_events = [record for record in records if record.get("event") == "request_received"]
    failed_events = [record for record in records if record.get("event") == "request_failed"]
    latencies = [float(record["latency_ms"]) for record in response_events if isinstance(record.get("latency_ms"), (int, float))]
    p95_latency_ms = percentile(latencies, 95)
    total_requests = len(request_events)
    error_rate_pct = len(failed_events) / total_requests * 100 if total_requests else 0.0
    pii_leaks = sorted({
        detector_name
        for record in records
        for detector_name, detector in PII_DETECTORS.items()
        if detector.search(json.dumps(record, ensure_ascii=False))
    })
    anomalies: list[dict[str, Any]] = []
    if pii_leaks:
        anomalies.append({"type": "pii_leak", "detected": pii_leaks})
    if p95_latency_ms > latency_slo_ms:
        anomalies.append({"type": "high_latency", "p95_latency_ms": p95_latency_ms, "slo_ms": latency_slo_ms})
    if error_rate_pct > error_slo_pct:
        anomalies.append({"type": "high_error_rate", "error_rate_pct": round(error_rate_pct, 2), "slo_pct": error_slo_pct})
    return {
        "records_analyzed": len(records),
        "requests": total_requests,
        "p95_latency_ms": p95_latency_ms,
        "error_rate_pct": round(error_rate_pct, 2),
        "pii_leaks": pii_leaks,
        "anomalies": anomalies,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Detect log anomalies against the lab SLOs.")
    parser.add_argument("--log-path", type=Path, default=DEFAULT_LOG_PATH)
    parser.add_argument("--slo-path", type=Path, default=DEFAULT_SLO_PATH)
    args = parser.parse_args()
    slo = yaml.safe_load(args.slo_path.read_text(encoding="utf-8"))
    slis = slo["slis"]
    summary = analyze_records(
        load_records(args.log_path),
        latency_slo_ms=float(slis["latency_p95_ms"]["objective"]),
        error_slo_pct=float(slis["error_rate_pct"]["objective"]),
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    raise SystemExit(1 if summary["anomalies"] else 0)


if __name__ == "__main__":
    main()
