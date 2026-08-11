# Bonus observability

## Cost optimization

`FakeLLM` giới hạn output ở `MAX_OUTPUT_TOKENS` (mặc định `200`) khi practice incident `cost_spike` bật. Đây là guardrail chống chi phí tăng đột biến; giá trị có thể cấu hình qua environment variable mà không sửa code.

Đo before/after với cùng 10 sample queries và `cost_spike`:

| Cấu hình | Output tokens | Total cost (USD) |
|---|---:|---:|
| Before: `MAX_OUTPUT_TOKENS=1000` | 5,696 | 0.0864 |
| After: `MAX_OUTPUT_TOKENS=200` | 2,000 | 0.0310 |

Chi phí giảm 64.1%. Chi tiết đo được lưu tại `submission/evidence/bonus-cost-optimization.md`.

## Audit log

`app.audit_logging.write_audit_event` ghi JSONL riêng vào `AUDIT_LOG_PATH` (mặc định `data/audit.jsonl`). App audit các sự kiện `configuration_loaded`, `incident_enabled`, và `incident_disabled`; mọi string đều đi qua PII scrubber trước khi ghi.

## Anomaly automation

Chạy:

```bash
python scripts/anomaly_check.py
```

Script đọc `data/logs.jsonl` và `config/slo.yaml`, kiểm tra raw PII, p95 latency và error rate. Nó in JSON summary, exit 0 khi không có anomaly và exit 1 khi phát hiện anomaly, nên có thể dùng trong CI hoặc cron.
