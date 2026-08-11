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
- Tổng số traces/correlation IDs quan sát được trong log local: 70 unique correlation IDs.
- Số PII leak còn lại: 0 theo `validate_logs.py`.
- Link/đường dẫn dashboard: `data/dashboard.html`.

## 3. Logging và tracing

- Evidence correlation ID: request PII probe trả về `correlation_id=req-c0ffee12`; log `response_sent` giữ cùng correlation ID.
- Evidence PII redaction: request kiểm thử chứa email/số điện thoại mẫu; log chỉ giữ `[REDACTED_EMAIL]` và `[REDACTED_PHONE_VN]`, `validate_logs.py` báo `Potential PII leaks detected: 0`.
- Evidence trace waterfall: phụ thuộc Langfuse/trace UI của phần CP2; cần bổ sung ảnh từ thành viên B hoặc từ môi trường trace khi bật Langfuse.
- Giải thích một span/log đáng chú ý: trong `rag_slow`, request `req-6c10f709` cho feature `refund` có latency cao; root cause là practice incident làm chậm retrieval.

## 4. Prompt versioning

- Prompt name: chờ evidence Langfuse từ phần CP2.
- Version/label baseline: chờ evidence Langfuse từ phần CP2.
- Version/label candidate: chờ evidence Langfuse từ phần CP2.
- Trace ID của mỗi version: chờ evidence Langfuse từ phần CP2.
- Bằng chứng đổi label hoặc rollback: chờ evidence Langfuse từ phần CP2.

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: `HOP LE: 6/6 panel co trong dashboard contract.`
- Evidence dashboard: `data/dashboard.html`, sinh bằng `python scripts/build_dashboard.py`.
- SLO đã chọn và lý do: theo `config/dashboard.yaml`: p95 latency <= 3000 ms, error rate <= 2%, total cost <= 2.5 USD, tokens <= 50000, quality mean >= 0.75; các SLO này bao phủ độ trễ, lỗi, chi phí và chất lượng trả lời.
- Alert rules và runbook: phụ thuộc phần CP2 của thành viên B; member C đã tạo evidence để B đối chiếu threshold/triệu chứng.

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
