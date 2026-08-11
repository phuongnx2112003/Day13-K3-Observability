# Cost optimization evidence

Ngày đo: 2026-08-11. Cùng 10 request trong `data/sample_queries.jsonl`, cùng incident `cost_spike`.

| Mốc | Cấu hình benchmark | `tokens_out_total` | `total_cost_usd` |
|---|---|---:|---:|
| Before | `MAX_OUTPUT_TOKENS=1000`, server `:8002` | 5696 | 0.0864 |
| After | `MAX_OUTPUT_TOKENS=200`, server `:8001` | 2000 | 0.0310 |

Kết quả: giảm `0.0554 USD` trên 10 request, tương đương **64.1%**. Guardrail được triển khai tại `app/mock_llm.py`; khi `cost_spike` nhân output tokens lên 4 lần, output bị giới hạn bởi `MAX_OUTPUT_TOKENS`.

Các response ở cả hai lượt đều HTTP 200. Sau mỗi benchmark, incident đã được disable.
