# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- Tên: HighLatencyAlert
- Severity: warning
- SLI/SLO liên quan: latency_p95_ms <= 3000ms
- Điều kiện và thời gian duy trì: latency_p95_ms > 3000ms kéo dài 5 phút
- Ảnh hưởng tới người dùng: Người dùng phải chờ quá lâu mới nhận được phản hồi từ Chatbot API.
- Ba bước kiểm tra đầu tiên:
  1. Kiểm tra Dashboard panel Latency percentiles để xác định đường P95/P99 tăng vọt từ thời điểm nào.
  2. Mở Langfuse Traces gần nhất, tìm các Trace có latency_ms > 3000ms và kiểm tra Span nào chiếm nhiều thời gian nhất (RAG retrieve hay LLM generate).
  3. Lọc log trong data/logs.jsonl theo correlation_id của Trace bị chậm để xem log chi tiết.
- Mitigation tạm thời: Nếu do RAG vector search bị nghẽn, bật feature flag fallback hoặc giảm top_k; nếu do Prompt v2 bị dài, tiến hành Rollback Prompt về v1.
- Owner: sre-team

## Alert 2

- Tên: HighErrorRateAlert
- Severity: critical
- SLI/SLO liên quan: error_rate_pct <= 2%
- Điều kiện và thời gian duy trì: error_rate_pct > 2% kéo dài 5 phút
- Ảnh hưởng tới người dùng: Người dùng nhận được lỗi HTTP 500 / Internal Server Error khi chat.
- Ba bước kiểm tra đầu tiên:
  1. Kiểm tra Dashboard panel Error rate and breakdown để xem loại lỗi nào chiếm tỉ lệ cao nhất (error_type).
  2. Mở Langfuse Traces lọc theo Status = ERROR để xem bước gọi API nào thất bại.
  3. Mở log data/logs.jsonl tìm các event request_failed để đọc ngoại lệ detail và stack trace.
- Mitigation tạm thời: Tắt kịch bản sự cố đang bật (/incidents/{name}/disable) hoặc restart service API.
- Owner: sre-team

## Alert 3

- Tên: LowQualityScoreAlert
- Severity: warning
- SLI/SLO liên quan: quality_score_avg >= 0.75
- Điều kiện và thời gian duy trì: quality_score_avg < 0.75 kéo dài 15 phút
- Ảnh hưởng tới người dùng: Phản hồi của Chatbot bị sai lệch, sơ sài hoặc không đúng ngữ cảnh RAG.
- Ba bước kiểm tra đầu tiên:
  1. Kiểm tra Dashboard panel Quality proxy để xem xu hướng giảm điểm.
  2. Mở Langfuse kiểm tra prompt_version và prompt_label đang chạy có vừa bị thay đổi gần đây không.
  3. Đọc mẫu 5 Trace có quality_score < 0.5 để xem câu trả lời và câu hỏi của người dùng.
- Mitigation tạm thời: Rollback Prompt production trên Langfuse về phiên bản ổn định trước đó (v1).
- Owner: sre-team

