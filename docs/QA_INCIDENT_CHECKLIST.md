# QA và điều tra incident — Thành viên C

## Practice incident

Với mỗi scenario, lưu lại thời điểm bắt đầu/kết thúc, command đã chạy và các giá trị trước/sau:

| Scenario | Triệu chứng cần xác nhận | Span/log cần tìm |
|---|---|---|
| `rag_slow` | P95 latency tăng rõ rệt | retrieval span, `response_sent.latency_ms` |
| `tool_fail` | Error rate tăng, có request 500 | `request_failed`, `error_type=RuntimeError` |
| `cost_spike` | Output tokens và cost tăng | generation usage, `response_sent.tokens_out/cost_usd` |

Chạy một scenario:

```bash
python scripts/inject_incident.py --scenario rag_slow
python scripts/load_test.py --concurrency 5
python scripts/validate_logs.py
```

Kết thúc practice:

```bash
python scripts/inject_incident.py --scenario rag_slow --disable
```

## Evidence tối thiểu

- Screenshot metric trước và trong incident.
- Trace ID/span bất thường.
- Log line có cùng `correlation_id`.
- Root cause, mitigation và preventive measure.
- Kết quả validator sau khi incident đã tắt.

## Sign-off của QA

- [ ] `/health` trả `ok: true`.
- [ ] `/chat` trả HTTP 200 khi không có incident.
- [ ] Mỗi request có correlation ID riêng.
- [ ] `validate_logs.py` đạt 100/100.
- [ ] Không còn PII nguyên văn.
- [ ] Dashboard validator đạt 6/6 panel.
- [ ] Incident đã được disable sau khi diễn tập.
- [ ] Evidence có thể truy ngược từ metric → trace → log.
