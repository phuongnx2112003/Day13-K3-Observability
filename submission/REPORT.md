# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm:
- Repository URL: https://github.com/phuongnx2112003/Day13-K3-Observability
- Commit SHA cuối: xem HEAD của branch `member-c-qa-chief-investigator` sau khi push cuối.
- Thành viên và vai trò:
  - Thành viên A: Tech Lead/Backend Engineer, phụ trách CP1 middleware, correlation ID, log enrichment.
  - Thành viên B: SRE & Alerts Engineer, phụ trách CP2 Langfuse, SLO/alert rules, alert runbook.
  - Thành viên C: QA & Chief Investigator, phụ trách dashboard spec/runtime evidence, load test, practice incident và tổng hợp báo cáo.

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 100/100.
- Tổng số traces/correlation IDs quan sát được trong log local: 47 unique correlation IDs.
- Số PII leak còn lại: 0 theo `validate_logs.py`.
- Link/đường dẫn dashboard: `data/dashboard.html`.

## 3. Logging và tracing

- Evidence correlation ID: request PII probe trả về `correlation_id=req-c0ffee12`; log `response_sent` giữ cùng correlation ID.
- Evidence PII redaction: request chứa `namhai@example.com` và `0912345678`; `validate_logs.py` báo `Potential PII leaks detected: 0`.
- Evidence trace waterfall: phụ thuộc Langfuse/trace UI của phần CP2; cần bổ sung ảnh từ thành viên B hoặc từ môi trường trace khi bật Langfuse.
- Giải thích một span/log đáng chú ý: trong `rag_slow`, request `req-6c10f709` cho feature `refund` có latency cao; root cause là practice incident làm chậm retrieval.

## 4. Prompt versioning

- Prompt name: `day13-chat`
- Version/label baseline: `Version 1` (Labels: `production`, `baseline`)
- Version/label candidate: `Version 2` (Labels: `candidate`, `latest`)
- Trace ID của mỗi version:
  - Version 1 (`baseline`): `5f657b8a34b38a79db77b0674e7ad4bf`
  - Version 2 (`candidate`): `req-5b679fc0`
- Bằng chứng đổi label hoặc rollback: [submission/evidence/evidence_rollback.png](file:///d:/Vin/Lab/B13/Day13-K3-Observability/submission/evidence/evidence_rollback.png) và [submission/evidence/evidence_prompt_versions.png](file:///d:/Vin/Lab/B13/Day13-K3-Observability/submission/evidence/evidence_prompt_versions.png)

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: `HỢP LỆ: 6/6 panel có trong dashboard contract.` (Ảnh bằng chứng: [submission/evidence/evidence_dashboard_validator.png](file:///d:/Vin/Lab/B13/Day13-K3-Observability/submission/evidence/evidence_dashboard_validator.png))
- Evidence dashboard: [submission/evidence/evidence_dashboard.png](file:///d:/Vin/Lab/B13/Day13-K3-Observability/submission/evidence/evidence_dashboard.png)
- SLO đã chọn và lý do:
  - `latency_p95_ms <= 3000ms`: Cam kết 99.5% request phản hồi dưới 3 giây để đảm bảo trải nghiệm người dùng không bị gián đoạn.
  - `error_rate_pct <= 2%`: Giữ tỉ lệ lỗi 500 dưới 2% (99% Uptime) để đảm bảo độ tin cậy của dịch vụ API.
  - `daily_cost_usd <= $2.5`: Khống chế ngân sách API gọi LLM hàng ngày không bị lãng phí token.
  - `quality_score_avg >= 0.75`: Đảm bảo 95% thời gian chất lượng câu trả lời RAG đạt mức độ chính xác cao.
- Alert rules và runbook: Cấu hình 3 Cảnh báo Symptom-based (`HighLatencyAlert`, `HighErrorRateAlert`, `LowQualityScoreAlert`) tại [config/alert_rules.yaml](file:///d:/Vin/Lab/B13/Day13-K3-Observability/config/alert_rules.yaml) và Runbook quy trình 3 bước xử lý sự cố (Metrics -> Traces -> Logs) tại [docs/alerts.md](file:///d:/Vin/Lab/B13/Day13-K3-Observability/docs/alerts.md).


## 6. Điều tra challenge

- Challenge ID: `day13-k3-observability-v1`.
- Triệu chứng từ metrics: khi bật `rag_slow`, challenge feature `refund` tăng latency rõ rệt; load test quan sát request khoảng 10.6s-13.3s.
- Trace ID liên quan: chưa có Langfuse trace ID vì tracing local đang `tracing_enabled=false`; dùng correlation ID trong log làm evidence local.
- Log line/correlation ID liên quan: `req-6c10f709`, `req-a4442afd`, `req-04dd78c0` cho feature `refund`, latency_ms log đại diện `2651`.
- Root cause: practice incident `rag_slow` làm chậm retrieval path cho challenge feature `refund`.
- Fix action: tắt incident bằng `python scripts/inject_incident.py --base-url http://127.0.0.1:8010 --scenario rag_slow --disable`, sau đó rerun load test/validator.
- Preventive measure: alert theo p95 latency SLO, điều tra bằng đường metric -> correlation ID -> log/trace retrieval.

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| C | Dashboard local, QA tests, incident practice checklist, custom-port QA scripts, evidence/report phần độc lập | Branch `member-c-qa-chief-investigator`, commits `8ccc8b0`, `26827e3`, `32288c3`, `f647b47`, `666d9fe` và commit evidence cuối | Observability cần nối được metric -> correlation ID -> log/trace, và script test phải không phụ thuộc cứng vào một port |
