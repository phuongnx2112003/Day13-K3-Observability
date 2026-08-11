from app import metrics


def test_percentile_basic() -> None:
    assert metrics.percentile([100, 200, 300, 400], 50) >= 100


def test_snapshot_calculates_error_rate(monkeypatch) -> None:
    monkeypatch.setattr(metrics, "TRAFFIC", 8)
    monkeypatch.setattr(metrics, "ERRORS", metrics.Counter({"RuntimeError": 2}))

    assert metrics.snapshot()["error_rate_pct"] == 20.0
