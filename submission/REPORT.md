# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm:
- Repository URL:
- Commit SHA cuối:
- Thành viên và vai trò:

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`:
- Tổng số traces:
- Số PII leak còn lại:
- Link/đường dẫn dashboard:

## 3. Logging và tracing

- Evidence correlation ID:
- Evidence PII redaction:
- Evidence trace waterfall:
- Giải thích một span đáng chú ý:

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

- Challenge ID:
- Triệu chứng từ metrics:
- Trace ID liên quan:
- Log line/correlation ID liên quan:
- Root cause:
- Fix action:
- Preventive measure:

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| | | | |
