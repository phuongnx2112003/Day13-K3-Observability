"""Build a lightweight, local observability dashboard from JSONL logs."""
from __future__ import annotations

import argparse
import html
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]


def percentile(values: list[float], p: int) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    index = min(len(values) - 1, max(0, round((p / 100) * len(values) + 0.5) - 1))
    return values[index]


def load_records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            records.append(item)
    return records


def build_html(records: list[dict], generated_at: str) -> str:
    responses = [r for r in records if r.get("event") == "response_sent"]
    requests = [r for r in records if r.get("event") == "request_received"]
    failures = [r for r in records if r.get("event") == "request_failed"]
    latency = [float(r["latency_ms"]) for r in responses if isinstance(r.get("latency_ms"), (int, float))]
    costs = [float(r["cost_usd"]) for r in responses if isinstance(r.get("cost_usd"), (int, float))]
    tokens_in = sum(r.get("tokens_in", 0) or 0 for r in responses)
    tokens_out = sum(r.get("tokens_out", 0) or 0 for r in responses)
    quality = [float(r["quality_score"]) for r in responses if isinstance(r.get("quality_score"), (int, float))]
    error_rate = (len(failures) / len(requests) * 100) if requests else 0.0
    quality_avg = mean(quality) if quality else 0.0
    cards = [
        ("P95 latency", f"{percentile(latency, 95):,.0f} ms" if latency else "N/A", "SLO ≤ 3,000 ms", percentile(latency, 95) <= 3000, bool(latency)),
        ("Traffic", f"{len(requests):,}" if requests else "N/A", "requests / window", True, bool(requests)),
        ("Error rate", f"{error_rate:.2f}%" if requests else "N/A", "SLO ≤ 2.00%", error_rate <= 2, bool(requests)),
        ("Total cost", f"${sum(costs):.4f}" if costs else "N/A", "budget ≤ $2.50", sum(costs) <= 2.5, bool(costs)),
        ("Tokens", f"{tokens_in + tokens_out:,}" if responses else "N/A", f"in {tokens_in:,} · out {tokens_out:,}", True, bool(responses)),
        ("Quality proxy", f"{quality_avg:.2f}" if quality else "N/A", "SLO ≥ 0.75", quality_avg >= 0.75, bool(quality)),
    ]
    card_html = "".join(
        f'<article class="card"><div class="card-top"><span>{html.escape(title)}</span>'
        f'<span class="status {"muted-status" if not has_data else ("ok" if ok else "bad")}">{"NO DATA" if not has_data else ("NOMINAL" if ok else "BREACH")}</span></div>'
        f'<div class="value">{value}</div><div class="hint">{html.escape(hint)}</div></article>'
        for title, value, hint, ok, has_data in cards
    )
    error_counts = Counter(str(r.get("error_type") or "unknown") for r in failures)
    error_rows = "".join(
        f"<tr><td>{html.escape(error_type)}</td><td>{count}</td></tr>"
        for error_type, count in error_counts.most_common()
    ) or '<tr><td colspan="2" class="muted">No failures in this window</td></tr>'
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="30">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Day 13 · AI Observability</title>
<style>
:root{{--bg:#0b1020;--panel:#121a2d;--line:#24304a;--text:#edf3ff;--muted:#8c9ab5;--cyan:#4fd1c5;--blue:#73a7ff;--red:#ff7187;--amber:#f6c85f}}
*{{box-sizing:border-box}} body{{margin:0;background:radial-gradient(circle at 90% 0%,#17284a 0,#0b1020 38%);color:var(--text);font:14px Inter,Segoe UI,Arial,sans-serif}}
.shell{{max-width:1440px;margin:auto;padding:34px 42px 52px}} .header{{display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:28px}}
.eyebrow{{color:var(--cyan);font-size:11px;letter-spacing:2px;text-transform:uppercase;font-weight:700}} h1{{font-size:30px;margin:7px 0 6px;letter-spacing:-.6px}} .subtitle,.muted{{color:var(--muted)}}
.window{{border:1px solid var(--line);background:#10182a;padding:11px 15px;border-radius:10px;text-align:right;color:var(--muted)}} .window strong{{display:block;color:var(--text);font-size:14px}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}} .card,.panel{{background:linear-gradient(145deg,rgba(23,34,58,.96),rgba(14,22,39,.96));border:1px solid var(--line);border-radius:14px;box-shadow:0 14px 35px #05091455}}
.card{{padding:18px 20px;min-height:132px}} .card-top{{display:flex;justify-content:space-between;color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.7px}} .status{{font-size:10px;font-weight:700;padding:4px 7px;border-radius:20px}} .ok{{background:#123d3a;color:var(--cyan)}} .bad{{background:#4b1d2a;color:var(--red)}} .muted-status{{background:#28344d;color:var(--muted)}} .value{{font-size:34px;font-weight:750;margin:15px 0 4px;letter-spacing:-1px}} .hint{{color:var(--muted);font-size:12px}}
.lower{{display:grid;grid-template-columns:1.3fr .7fr;gap:14px;margin-top:14px}} .panel{{padding:22px}} h2{{font-size:15px;margin:0 0 5px}} .panel-note{{color:var(--muted);font-size:12px;margin-bottom:18px}} table{{width:100%;border-collapse:collapse}} td{{padding:12px 0;border-bottom:1px solid var(--line)}} td:last-child{{text-align:right;color:var(--amber)}}
.bar-row{{display:grid;grid-template-columns:120px 1fr 70px;gap:12px;align-items:center;margin:17px 0;color:var(--muted);font-size:12px}} .bar{{height:8px;background:#263553;border-radius:9px;overflow:hidden}} .fill{{height:100%;background:linear-gradient(90deg,var(--blue),var(--cyan));border-radius:9px}} .footer{{margin-top:22px;color:var(--muted);font-size:11px;display:flex;justify-content:space-between}}
@media(max-width:900px){{.shell{{padding:24px 18px}}.header{{display:block}}.window{{margin-top:18px;text-align:left;display:inline-block}}.grid,.lower{{grid-template-columns:1fr}}}}
</style></head><body><main class="shell"><header class="header"><div><div class="eyebrow">Day 13 · Production Readiness</div><h1>AI Observability Command Center</h1><div class="subtitle">A decision-focused view of reliability, efficiency and answer quality.</div></div><div class="window"><strong>Last 60 minutes</strong>Auto-refresh · 30 seconds</div></header>
<section class="grid">{card_html}</section><section class="lower"><article class="panel"><h2>Token consumption</h2><div class="panel-note">Total volume by direction · unit: tokens</div><div class="bar-row"><span>Input</span><div class="bar"><div class="fill" style="width:{min(100, tokens_in / max(tokens_in + tokens_out, 1) * 100):.1f}%"></div></div><strong>{tokens_in:,}</strong></div><div class="bar-row"><span>Output</span><div class="bar"><div class="fill" style="width:{min(100, tokens_out / max(tokens_in + tokens_out, 1) * 100):.1f}%"></div></div><strong>{tokens_out:,}</strong></div><div class="footer"><span>Source: response_sent</span><span>Generated {html.escape(generated_at)}</span></div></article><article class="panel"><h2>Error breakdown</h2><div class="panel-note">User-impacting failures · unit: events</div><table><thead><tr><td>Error type</td><td>Count</td></tr></thead><tbody>{error_rows}</tbody></table><div class="footer"><span>Threshold</span><span>≤ 2.00%</span></div></article></section></main></body></html>'''


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Day 13 local dashboard")
    parser.add_argument("--logs", type=Path, default=ROOT / "data" / "logs.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "dashboard.html")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build_html(load_records(args.logs), datetime.now(timezone.utc).isoformat()), encoding="utf-8")
    print(f"Dashboard written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
