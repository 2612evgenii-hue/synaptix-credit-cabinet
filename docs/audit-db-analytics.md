# Аудит зоны «данные и аналитика» (NamePantrer / ТЗ Петра)

Дата: 2026-10-20. Ветка: `feat/4-persistence-seed`.  
Scope: БД, синтетика, моки, риск/решение, extract+explain (REQ-20).  
Вне зоны: HTTP API, веб-UI, Compose web (Евгений).

## Вердикт

**ТЗ Петра по зоне данных/аналитики/ИИ — закрыто на уровне библиотеки и артефактов передачи.**  
Интеграция в веб и замеры Ollama на железе команды — у Евгения / третий участник.

Финальные проверки: **`147 passed`** (`apps/api`), **`ai/eval` score=5/5**.  
Adversarial: decision 1–13 + explain A1–A6 + extract **B1–B2 fixed, B3 CLEAN**.

## Чеклист P01–P12

| ID | Статус | Артефакт |
| --- | --- | --- |
| P01 контракты | Готово | `contracts/*.schema.json`, `contracts/examples/` |
| P02 модель + словарь | Готово | `docs/data-model.md`, `docs/data-dictionary.md`, ORM/Alembic |
| P03 продукты | Готово | `data/products.json` + seed |
| P04 синтетика | Готово* | `scenarios.json`, `expected-results.json`, `manifest.json` (*3 сценария, не 12–20) |
| P05 симуляторы | Готово | `mocks.py` + `contracts/checks.schema.json` |
| P06 расчёты | Готово | `docs/calculations.md` + `decision.py` |
| P07 правила | Готово | `docs/credit-policy.md` + reason_codes |
| P08 метрики | Готово | `docs/metrics.md` |
| P09 LLM runtime | Готово* | `ai/model-manifest.json`, `docs/ai-runtime.md` (*замеры hardware = pending) |
| P10 extract | Готово | `analytics/extract.py`, heuristic default, confirm required |
| P11 eval | Готово | `ai/eval/`, `docs/ai-evaluation.md` |
| P12 передача | Готово* | README зоны, THIRD_PARTY, docs (*Docker/Ollama compose — infra) |

## Инварианты

- Score ≠ decision; null ≠ 0; unavailable ≠ reject  
- LLM не пишет `DecisionResult.outcome`  
- Extract: `needs_user_confirm=true`; injection не задаёт сумму; FX ≠ RUB  
- Review build без скачивания модели (`LLM_BACKEND=template`)

## Долг (не блокеры зоны)

1. Расширить seed до 12–20 компаний (P04 ориентир).  
2. Заполнить таблицу замеров в `docs/ai-runtime.md` на ПК команды.  
3. Compose-сервис Ollama + pin sha весов после первого pull.  
4. Подключение extract/decision к HTTP — зона Евгения.
