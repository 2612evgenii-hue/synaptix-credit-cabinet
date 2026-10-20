# Метрики MVP (определения)

Все цифры на seed — показатели **тестового набора**, не реальная конверсия.

| Метрика | Определение |
| --- | --- |
| submitted_apps | Уникальные заявки, впервые ушедшие из DRAFT/SUBMITTED в пайплайн рассмотрения |
| needs_info_apps | Уникальные заявки с outcome/event NEEDS_INFO (повтор не умножает) |
| approve_rate | APPROVED / (APPROVED + REJECTED); незавершённые исключены; при нуле знаменателя — undefined |
| time_to_decision | От первой отправки до финального outcome (ожидание клиента отдельно помечать) |
| extract_success | Доля eval-кейсов, где все целевые поля совпали (`ai/eval`) |
| ai_latency | Время extract/explain; cold start отдельно |

Пример SQL (после появления событий в прод-БД):

```sql
-- approve_rate on decisions for demo seed window
SELECT
  COUNT(*) FILTER (WHERE outcome = 'APPROVED')::float
  / NULLIF(COUNT(*) FILTER (WHERE outcome IN ('APPROVED','REJECTED')), 0)
FROM decisions;
```

Ожидаемые исходы seed: см. `data/expected-results.json`.
