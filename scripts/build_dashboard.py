"""Build a React-powered local observability dashboard from JSONL logs."""
from __future__ import annotations

import argparse
import html
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from string import Template

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


def status(ok: bool, has_data: bool = True) -> str:
    if not has_data:
        return "NO DATA"
    return "NOMINAL" if ok else "BREACH"


def dashboard_model(records: list[dict], generated_at: str) -> dict:
    responses = [r for r in records if r.get("event") == "response_sent"]
    requests = [r for r in records if r.get("event") == "request_received"]
    failures = [r for r in records if r.get("event") == "request_failed"]
    latency = [
        float(r["latency_ms"])
        for r in responses
        if isinstance(r.get("latency_ms"), (int, float))
    ]
    costs = [
        float(r["cost_usd"])
        for r in responses
        if isinstance(r.get("cost_usd"), (int, float))
    ]
    quality = [
        float(r["quality_score"])
        for r in responses
        if isinstance(r.get("quality_score"), (int, float))
    ]
    tokens_in = sum(int(r.get("tokens_in", 0) or 0) for r in responses)
    tokens_out = sum(int(r.get("tokens_out", 0) or 0) for r in responses)
    p95 = percentile(latency, 95)
    error_rate = (len(failures) / len(requests) * 100) if requests else 0.0
    quality_avg = mean(quality) if quality else 0.0
    total_cost = sum(costs)
    total_tokens = tokens_in + tokens_out
    error_counts = Counter(str(r.get("error_type") or "unknown") for r in failures)
    feature_counts = Counter(str(r.get("feature") or "unknown") for r in requests)
    unique_correlation_ids = {
        r.get("correlation_id")
        for r in records
        if r.get("correlation_id") and r.get("correlation_id") != "MISSING"
    }

    return {
        "generatedAt": generated_at,
        "window": {"label": "Last 60 minutes", "refreshSeconds": 30},
        "summary": {
            "records": len(records),
            "requests": len(requests),
            "responses": len(responses),
            "failures": len(failures),
            "correlationIds": len(unique_correlation_ids),
        },
        "cards": [
            {
                "id": "latency",
                "label": "P95 latency",
                "value": f"{p95:,.0f} ms" if latency else "N/A",
                "subvalue": "SLO <= 3,000 ms",
                "status": status(p95 <= 3000, bool(latency)),
                "tone": "good" if latency and p95 <= 3000 else ("bad" if latency else "muted"),
                "progress": min(100, p95 / 3000 * 100) if latency else 0,
            },
            {
                "id": "traffic",
                "label": "Traffic",
                "value": f"{len(requests):,}" if requests else "N/A",
                "subvalue": "requests / window",
                "status": status(True, bool(requests)),
                "tone": "good" if requests else "muted",
                "progress": min(100, len(requests) / 50 * 100) if requests else 0,
            },
            {
                "id": "errors",
                "label": "Error rate",
                "value": f"{error_rate:.2f}%" if requests else "N/A",
                "subvalue": "SLO <= 2.00%",
                "status": status(error_rate <= 2, bool(requests)),
                "tone": "good" if requests and error_rate <= 2 else ("bad" if requests else "muted"),
                "progress": min(100, error_rate / 2 * 100) if requests else 0,
            },
            {
                "id": "cost",
                "label": "Total cost",
                "value": f"${total_cost:.4f}" if costs else "N/A",
                "subvalue": "budget <= $2.50",
                "status": status(total_cost <= 2.5, bool(costs)),
                "tone": "good" if costs and total_cost <= 2.5 else ("bad" if costs else "muted"),
                "progress": min(100, total_cost / 2.5 * 100) if costs else 0,
            },
            {
                "id": "tokens",
                "label": "Tokens",
                "value": f"{total_tokens:,}" if responses else "N/A",
                "subvalue": f"in {tokens_in:,} / out {tokens_out:,}",
                "status": status(True, bool(responses)),
                "tone": "good" if responses else "muted",
                "progress": min(100, total_tokens / 50000 * 100) if responses else 0,
            },
            {
                "id": "quality",
                "label": "Quality proxy",
                "value": f"{quality_avg:.2f}" if quality else "N/A",
                "subvalue": "SLO >= 0.75",
                "status": status(quality_avg >= 0.75, bool(quality)),
                "tone": "good" if quality and quality_avg >= 0.75 else ("bad" if quality else "muted"),
                "progress": min(100, quality_avg * 100) if quality else 0,
            },
        ],
        "tokens": {"input": tokens_in, "output": tokens_out},
        "errors": [
            {"type": error_type, "count": count}
            for error_type, count in error_counts.most_common()
        ],
        "features": [
            {"feature": feature, "count": count}
            for feature, count in feature_counts.most_common()
        ],
        "investigation": {
            "primarySignal": "HighErrorRateAlert" if failures else "LatencyWatch",
            "rootCauseHint": "tool_fail practice incident" if failures else "rag_slow / latency path",
            "joinKey": "correlation_id",
        },
    }


def fallback_html(model: dict) -> str:
    cards = "".join(
        '<article class="metric-card">'
        f'<div class="metric-head"><span>{html.escape(card["label"])}</span>'
        f'<span class="pill {html.escape(card["tone"])}">{html.escape(card["status"])}</span></div>'
        f'<strong>{html.escape(card["value"])}</strong>'
        f'<small>{html.escape(card["subvalue"])}</small>'
        '<div class="meter"><span style="width:'
        f'{float(card["progress"]):.1f}%"></span></div></article>'
        for card in model["cards"]
    )
    errors = "".join(
        f'<tr><td>{html.escape(row["type"])}</td><td>{row["count"]}</td></tr>'
        for row in model["errors"]
    ) or '<tr><td colspan="2">No failures in this window</td></tr>'
    features = "".join(
        f'<li><span>{html.escape(row["feature"])}</span><strong>{row["count"]}</strong></li>'
        for row in model["features"]
    ) or "<li><span>No traffic</span><strong>0</strong></li>"
    return (
        '<main class="shell">'
        '<header class="topbar"><section><p class="eyebrow">Day 13 / AI Operations</p>'
        '<h1>Observability Command Center</h1>'
        '<p class="subtitle">Production-readiness view across reliability, spend, traffic, and answer quality.</p>'
        '</section><aside class="runtime"><span>Last 60 minutes</span><strong>30s refresh</strong></aside></header>'
        f'<section class="scoreboard">{cards}</section>'
        '<section class="workbench"><article class="panel wide"><div class="panel-title"><h2>Token mix</h2>'
        '<span>response_sent</span></div>'
        f'<div class="token-stack"><div style="--size:{model["tokens"]["input"]}"><span>Input</span><strong>{model["tokens"]["input"]:,}</strong></div>'
        f'<div style="--size:{model["tokens"]["output"]}"><span>Output</span><strong>{model["tokens"]["output"]:,}</strong></div></div>'
        f'<p class="generated">Generated {html.escape(model["generatedAt"])}</p></article>'
        '<article class="panel"><div class="panel-title"><h2>Error breakdown</h2><span>SLO <= 2%</span></div>'
        f'<table>{errors}</table></article>'
        '<article class="panel"><div class="panel-title"><h2>Traffic by feature</h2><span>request_received</span></div>'
        f'<ul class="feature-list">{features}</ul></article></section></main>'
    )


HTML_TEMPLATE = Template(
    """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="30">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Day 13 / React Observability Dashboard</title>
<style>
:root {
  color-scheme: dark;
  --bg: #0b0d12;
  --panel: #151922;
  --panel-2: #11151e;
  --line: #2a3242;
  --text: #f2f5f9;
  --muted: #9aa4b5;
  --green: #2dd4bf;
  --red: #fb7185;
  --amber: #fbbf24;
  --blue: #60a5fa;
  --violet: #a78bfa;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  min-height: 100vh;
  background:
    linear-gradient(180deg, rgba(32, 38, 52, .92), rgba(11, 13, 18, 1) 38%),
    #0b0d12;
  color: var(--text);
  font: 14px Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Arial, sans-serif;
}
.shell { max-width: 1480px; margin: 0 auto; padding: 30px 34px 44px; }
.topbar { display: grid; grid-template-columns: 1fr auto; gap: 22px; align-items: end; margin-bottom: 24px; }
.eyebrow { margin: 0 0 9px; color: var(--green); font-size: 12px; font-weight: 800; letter-spacing: .16em; text-transform: uppercase; }
h1 { margin: 0; font-size: clamp(30px, 4vw, 54px); line-height: .98; letter-spacing: 0; }
.subtitle { margin: 13px 0 0; color: var(--muted); max-width: 720px; font-size: 16px; }
.runtime { border: 1px solid var(--line); background: rgba(17, 21, 30, .82); border-radius: 8px; padding: 14px 16px; min-width: 190px; text-align: right; }
.runtime span, .runtime strong { display: block; }
.runtime span { color: var(--muted); }
.scoreboard { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 10px; }
.metric-card, .panel {
  background: linear-gradient(180deg, rgba(25, 30, 41, .98), rgba(17, 21, 30, .98));
  border: 1px solid var(--line);
  border-radius: 8px;
  box-shadow: 0 18px 44px rgba(0, 0, 0, .24);
}
.metric-card { min-height: 170px; padding: 16px; display: flex; flex-direction: column; justify-content: space-between; }
.metric-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; color: var(--muted); font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: .08em; }
.pill { border-radius: 999px; padding: 4px 7px; font-size: 10px; font-weight: 900; letter-spacing: .04em; }
.pill.good { background: rgba(45, 212, 191, .14); color: var(--green); }
.pill.bad { background: rgba(251, 113, 133, .16); color: var(--red); }
.pill.muted { background: rgba(154, 164, 181, .12); color: var(--muted); }
.metric-card strong { display: block; font-size: 30px; line-height: 1; letter-spacing: 0; margin-top: 18px; }
.metric-card small { color: var(--muted); font-size: 12px; }
.meter { height: 5px; background: #252c3a; border-radius: 999px; overflow: hidden; margin-top: 14px; }
.meter span { display: block; height: 100%; background: linear-gradient(90deg, var(--blue), var(--green)); border-radius: inherit; }
.metric-card:has(.pill.bad) .meter span { background: linear-gradient(90deg, var(--amber), var(--red)); }
.workbench { display: grid; grid-template-columns: 1.35fr .8fr .85fr; gap: 10px; margin-top: 10px; }
.panel { padding: 18px; min-height: 270px; }
.panel-title { display: flex; justify-content: space-between; gap: 12px; align-items: baseline; border-bottom: 1px solid var(--line); padding-bottom: 12px; margin-bottom: 18px; }
h2 { margin: 0; font-size: 16px; letter-spacing: 0; }
.panel-title span, .generated { color: var(--muted); font-size: 12px; }
.token-stack { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; align-items: end; height: 160px; }
.token-stack div { align-self: end; min-height: 44px; height: min(100%, calc(44px + var(--size) * .018px)); border-radius: 8px; padding: 12px; background: linear-gradient(180deg, rgba(96,165,250,.96), rgba(45,212,191,.68)); display: flex; flex-direction: column; justify-content: flex-end; }
.token-stack div + div { background: linear-gradient(180deg, rgba(167,139,250,.96), rgba(96,165,250,.68)); }
.token-stack span { color: rgba(255,255,255,.78); }
.token-stack strong { font-size: 26px; letter-spacing: 0; }
table { width: 100%; border-collapse: collapse; }
td { padding: 12px 0; border-bottom: 1px solid var(--line); }
td:last-child { color: var(--amber); text-align: right; font-weight: 800; }
.feature-list { list-style: none; padding: 0; margin: 0; display: grid; gap: 10px; }
.feature-list li { display: flex; justify-content: space-between; gap: 12px; padding: 11px 0; border-bottom: 1px solid var(--line); color: var(--muted); }
.feature-list strong { color: var(--text); }
.investigation { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 10px; }
.signal { border: 1px solid var(--line); background: rgba(17, 21, 30, .7); border-radius: 8px; padding: 14px; }
.signal span { display: block; color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: .08em; margin-bottom: 8px; }
.signal strong { font-size: 15px; }
@media (max-width: 1180px) { .scoreboard { grid-template-columns: repeat(3, 1fr); } .workbench { grid-template-columns: 1fr; } }
@media (max-width: 760px) { .shell { padding: 22px 16px 32px; } .topbar { grid-template-columns: 1fr; } .runtime { text-align: left; } .scoreboard, .investigation { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<div id="root">$fallback</div>
<script id="dashboard-data" type="application/json">$data</script>
<script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
<script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
<script>
(function () {
  const raw = document.getElementById("dashboard-data").textContent;
  const data = JSON.parse(raw);
  if (!window.React || !window.ReactDOM) return;
  const h = React.createElement;
  function MetricCard({ card }) {
    return h("article", { className: "metric-card" },
      h("div", { className: "metric-head" },
        h("span", null, card.label),
        h("span", { className: "pill " + card.tone }, card.status)
      ),
      h("div", null,
        h("strong", null, card.value),
        h("small", null, card.subvalue),
        h("div", { className: "meter" }, h("span", { style: { width: card.progress + "%" } }))
      )
    );
  }
  function PanelTitle({ title, note }) {
    return h("div", { className: "panel-title" }, h("h2", null, title), h("span", null, note));
  }
  function App() {
    const totalTokens = Math.max(1, data.tokens.input + data.tokens.output);
    return h("main", { className: "shell" },
      h("header", { className: "topbar" },
        h("section", null,
          h("p", { className: "eyebrow" }, "Day 13 / AI Operations"),
          h("h1", null, "Observability Command Center"),
          h("p", { className: "subtitle" }, "Production-readiness view across reliability, spend, traffic, and answer quality.")
        ),
        h("aside", { className: "runtime" }, h("span", null, data.window.label), h("strong", null, data.window.refreshSeconds + "s refresh"))
      ),
      h("section", { className: "scoreboard" }, data.cards.map(card => h(MetricCard, { key: card.id, card }))),
      h("section", { className: "workbench" },
        h("article", { className: "panel wide" },
          h(PanelTitle, { title: "Token mix", note: "response_sent" }),
          h("div", { className: "token-stack" },
            h("div", { style: { "--size": data.tokens.input } }, h("span", null, "Input"), h("strong", null, data.tokens.input.toLocaleString())),
            h("div", { style: { "--size": data.tokens.output } }, h("span", null, "Output"), h("strong", null, data.tokens.output.toLocaleString()))
          ),
          h("p", { className: "generated" }, "Generated " + data.generatedAt)
        ),
        h("article", { className: "panel" },
          h(PanelTitle, { title: "Error breakdown", note: "SLO <= 2%" }),
          h("table", null, h("tbody", null, (data.errors.length ? data.errors : [{ type: "No failures in this window", count: "" }]).map(row => h("tr", { key: row.type }, h("td", null, row.type), h("td", null, row.count)))))
        ),
        h("article", { className: "panel" },
          h(PanelTitle, { title: "Traffic by feature", note: "request_received" }),
          h("ul", { className: "feature-list" }, (data.features.length ? data.features : [{ feature: "No traffic", count: 0 }]).map(row => h("li", { key: row.feature }, h("span", null, row.feature), h("strong", null, row.count))))
        )
      ),
      h("section", { className: "investigation" },
        h("div", { className: "signal" }, h("span", null, "Primary signal"), h("strong", null, data.investigation.primarySignal)),
        h("div", { className: "signal" }, h("span", null, "Join key"), h("strong", null, data.investigation.joinKey)),
        h("div", { className: "signal" }, h("span", null, "Root-cause hint"), h("strong", null, data.investigation.rootCauseHint))
      )
    );
  }
  ReactDOM.createRoot(document.getElementById("root")).render(h(App));
})();
</script>
</body>
</html>
"""
)


def build_html(records: list[dict], generated_at: str) -> str:
    model = dashboard_model(records, generated_at)
    return HTML_TEMPLATE.substitute(
        data=html.escape(json.dumps(model, ensure_ascii=False)),
        fallback=fallback_html(model),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Day 13 React dashboard")
    parser.add_argument("--logs", type=Path, default=ROOT / "data" / "logs.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "dashboard.html")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    args.output.write_text(build_html(load_records(args.logs), generated_at), encoding="utf-8")
    print(f"Dashboard written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
