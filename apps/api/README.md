# Backend · зона данных и аналитики

Ответственный: **NamePantrer**. Scope: PostgreSQL-модель, миграции, seed,
локальные моки проверок, **оценка риска** и **правила решения** (score ≠ decision).

Вне зоны: HTTP API lifecycle, веб-UI, Docker web (Issues #5/#7/#9 — другие участники).

## Пакеты

| Путь | Назначение |
| --- | --- |
| `src/synaptix_api/models` | ORM по `docs/data-model.md` |
| `src/synaptix_api/db` | session, seed, passwords |
| `src/synaptix_api/analytics` | mocks, risk, decision, extract, explain, pipeline, persist |
| `../../contracts` | JSON Schema extract/checks/decision |
| `../../data/products.json` | каталог демо-продуктов |
| `../../ai/` | prompts, model-manifest, eval |
| `alembic/` | миграции `20261020_0001`…`0004` |
| `tests/` | юнит/интеграция БД и аналитики |
| `docker-compose.postgres-verify.yml` | временный Postgres для AI01 (не product Compose) |

## Установка и тесты

```sh
cd apps/api
python -m pip install -r requirements.txt
set PYTHONPATH=src
set LLM_BACKEND=template
python -m pytest -q
python -m pytest tests/test_extract_qa_phrases.py -q
```

SQLite in-memory используется в pytest (`create_all`). Целевая проверка PostgreSQL (AI01):

```sh
docker compose -f docker-compose.postgres-verify.yml up -d
set DATABASE_URL=postgresql+psycopg2://synaptix:synaptix@127.0.0.1:54329/synaptix_verify
set APP_ENV=demo
python scripts/verify_postgres_ai01.py --write-log
docker compose -f docker-compose.postgres-verify.yml down -v
```

Демо-пароль seed: `demo1234`. Handoff: `docs/handoff-p0-ai-data.md`.

## Аналитика (кратко)

- `assess_risk` → score 0..100 + factors; отсутствие полей **не** подменяется нулём.
- `apply_decision_rules` → APPROVED / REJECTED / NEEDS_INFO / ALTERNATIVE / CHECK_UNAVAILABLE.
- `extract_application_fields` → цель/сумма/срок из текста (P10); всегда
  `needs_user_confirm=true`. Default — heuristic; Ollama опционален.
- `explain_decision` → текст для клиента/банка **после** решения (REQ-20).
  По умолчанию `LLM_BACKEND=template`. Опционально Ollama + `qwen3:4b`
  (см. `ai/model-manifest.json`). Сбой LLM не ломает кредитный путь.
- `unavailable` мока ≠ кредитный отказ.
- ADR-0002: PostgreSQL + SQLAlchemy.
