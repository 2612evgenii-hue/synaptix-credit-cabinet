# Оценка AI (extract) — P11

## Набор

- Файл: `ai/eval/cases.json` (held_out_v1, 5 кейсов для CI)
- Скрипт: `python ai/eval/evaluate.py` из корня репо (PYTHONPATH через скрипт)

## Текущий результат (heuristic backend)

Запускается без Ollama. Фактический score печатает скрипт (`score=N/M`).

Покрытые классы: однозначный extract, missing term, correction «не X а Y», prompt-injection (флаг, без смены решения), пустой запрос → missing_fields.

## Ориентир ТЗ

≥90% на однозначных контрольных — цель на расширенном наборе (30–60 фраз от третьего участника). Текущий CI-набор маленький и служит регрессией контракта.

## Ограничения

- Heuristic не заменяет качественный Qwen3 на свободной речи.
- `needs_user_confirm=true` всегда — UI обязан подтвердить поля.
- LLM не пишет Decision; injection не даёт одобрения.
