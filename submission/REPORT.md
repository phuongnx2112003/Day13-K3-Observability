# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: 2k345
- Repository URL: https://github.com/phuongnx2112003/Day13-K3-Observability
- Commit SHA evidence logging/validation: `5c66c9b` (74 correlation IDs unique, validator 100/100).
- Thành viên và vai trò:
  - Thành viên A — Nguyễn Xuân Phượng (2A202601874): Tech Lead/Backend Engineer, phụ trách CP1 middleware, correlation ID, log enrichment.
  - Thành viên B — Nguyễn Đào Nam Hải (2A202601037): Dashboard/QA & Chief Investigator, phụ trách dashboard spec/runtime evidence, load test, practice incident và tổng hợp báo cáo.
  - Thành viên C — Lê Nguyễn Minh Đức (2A202601013): SRE & Alerts Engineer, phụ trách CP2 Langfuse, SLO/alert rules, alert runbook.

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 100/100.
- Tổng số traces/correlation IDs quan sát được trong log local: 74 unique correlation IDs.
- Số PII leak còn lại: 0 theo `validate_logs.py`.
- Link/đường dẫn dashboard: `data/dashboard.html` (React-powered local dashboard).

## 3. Logging và tracing

- Evidence correlation ID: request PII probe trả về `correlation_id=req-c0ffee12`; log `response_sent` giữ cùng correlation ID.
- Evidence PII redaction: request kiểm thử chứa email/số điện thoại mẫu; log chỉ giữ `[REDACTED_EMAIL]` và `[REDACTED_PHONE_VN]`, `validate_logs.py` báo `Potential PII leaks detected: 0`.
- Evidence trace waterfall/metadata: `submission/evidence/evidence_trace_metadata.png`.
- Giải thích một span/log đáng chú ý: trong `rag_slow`, request `req-6c10f709` cho feature `refund` có latency cao; root cause là practice incident làm chậm retrieval.

## 4. Prompt versioning

- Prompt name: `day13-chat`
- Version/label baseline: `Version 1` (Labels: `production`, `baseline`)
- Version/label candidate: `Version 2` (Labels: `candidate`, `latest`)
- Trace ID của mỗi version:
  - Version 1 (`baseline`): `5f657b8a34b38a79db77b0674e7ad4bf`
  - Version 2 (`candidate`): `req-5b679fc0`
- Bằng chứng đổi label hoặc rollback: `submission/evidence/evidence_rollback.png` và `submission/evidence/evidence_prompt_versions.png`.

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: `HỢP LỆ: 6/6 panel có trong dashboard contract.`
- Evidence dashboard: `data/dashboard.html`, sinh bằng `python scripts/build_dashboard.py`; giao diện dùng ReactJS với fallback HTML tĩnh để vẫn mở được khi CDN chưa tải.
- SLO đã chọn và lý do:
  - `latency_p95_ms <= 3000ms`: Cam kết 99.5% request phản hồi dưới 3 giây để đảm bảo trải nghiệm người dùng không bị gián đoạn.
  - `error_rate_pct <= 2%`: Giữ tỉ lệ lỗi 500 dưới 2% (99% Uptime) để đảm bảo độ tin cậy của dịch vụ API.
  - `daily_cost_usd <= $2.5`: Khống chế ngân sách API gọi LLM hàng ngày không bị lãng phí token.
  - `quality_score_avg >= 0.75`: Đảm bảo 95% thời gian chất lượng câu trả lời RAG đạt mức độ chính xác cao.
- Alert rules và runbook: cấu hình 3 cảnh báo symptom-based (`HighLatencyAlert`, `HighErrorRateAlert`, `LowQualityScoreAlert`) tại `config/alert_rules.yaml` và runbook xử lý sự cố theo luồng Metrics -> Traces -> Logs tại `docs/alerts.md`.


## 6. Điều tra challenge

- Challenge ID: `day13-k3-observability-v1`.
- Triệu chứng từ metrics: khi bật `rag_slow`, challenge feature `refund` tăng latency rõ rệt; load test quan sát request khoảng 10.6s-13.3s.
- Trace ID liên quan: dùng Langfuse evidence từ `submission/evidence/evidence_trace_metadata.png`; evidence local dùng correlation ID trong log để đối chiếu.
- Log line/correlation ID liên quan: `req-6c10f709`, `req-a4442afd`, `req-04dd78c0` cho feature `refund`, latency_ms log đại diện `2651`.
- Root cause: practice incident `rag_slow` làm chậm retrieval path cho challenge feature `refund`.
- Fix action: tắt incident bằng `python scripts/inject_incident.py --base-url http://127.0.0.1:8010 --scenario rag_slow --disable`, sau đó rerun load test/validator.
- Preventive measure: alert theo p95 latency SLO, điều tra bằng đường metric -> correlation ID -> log/trace retrieval.

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR đã đối chiếu | Điều đã học |
|---|---|---|---|
| Nguyễn Xuân Phượng — A | Middleware correlation ID, structured logging, metadata enrichment, PII redaction evidence | Direct commits trên `main`: [`f7ef456`](https://github.com/phuongnx2112003/Day13-K3-Observability/commit/f7ef456), [`b54d729`](https://github.com/phuongnx2112003/Day13-K3-Observability/commit/b54d729), [`489dfea`](https://github.com/phuongnx2112003/Day13-K3-Observability/commit/489dfea). Không có PR riêng. | Log cần đủ context nhưng không được để lộ PII |
| Nguyễn Đào Nam Hải — B | Dashboard local, QA tests, incident practice checklist, custom-port QA scripts, evidence/report | [`PR #1`](https://github.com/phuongnx2112003/Day13-K3-Observability/pull/1) và [`PR #3`](https://github.com/phuongnx2112003/Day13-K3-Observability/pull/3); commits [`8ccc8b0`](https://github.com/phuongnx2112003/Day13-K3-Observability/commit/8ccc8b0), [`26827e3`](https://github.com/phuongnx2112003/Day13-K3-Observability/commit/26827e3), [`32288c3`](https://github.com/phuongnx2112003/Day13-K3-Observability/commit/32288c3), [`f647b47`](https://github.com/phuongnx2112003/Day13-K3-Observability/commit/f647b47), [`666d9fe`](https://github.com/phuongnx2112003/Day13-K3-Observability/commit/666d9fe), [`4f8f501`](https://github.com/phuongnx2112003/Day13-K3-Observability/commit/4f8f501). | Observability cần nối được metric -> correlation ID -> log/trace, và script test phải không phụ thuộc cứng vào một port |
| Lê Nguyễn Minh Đức — C | Langfuse trace/prompt evidence, SLO, alert rules, runbook | [`PR #2`](https://github.com/phuongnx2112003/Day13-K3-Observability/pull/2); commit [`37e6d0d`](https://github.com/phuongnx2112003/Day13-K3-Observability/commit/37e6d0d), kèm evidence prompt/rollback/trace trong `submission/evidence/`. | Alert tốt nên dựa trên triệu chứng/SLO và nối được Metrics -> Traces -> Logs |
