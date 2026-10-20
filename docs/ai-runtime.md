# Локальный LLM runtime (P09)

## Рекомендация

1. Установить [Ollama](https://ollama.com/).
2. `ollama pull qwen3:4b` (кандидат из `ai/model-manifest.json`; зафиксировать sha после pull).
3. `set LLM_BACKEND=ollama`
4. `set LLM_MODEL=qwen3:4b`
5. `set LLM_BASE_URL=http://127.0.0.1:11434`

Без модели: `LLM_BACKEND=template` — extract = heuristic, explain = rules template.

## Замеры (заполнить на машине команды)

| Параметр | Значение |
| --- | --- |
| OS | _pending_ |
| CPU | _pending_ |
| RAM | _pending_ |
| GPU | _pending_ |
| cold_start_s | _pending_ |
| p50_latency_s | _pending_ |
| peak_rss_mb | _pending_ |

Paid/cloud hosts блокируются в коде (`explain._host_allowed`).
