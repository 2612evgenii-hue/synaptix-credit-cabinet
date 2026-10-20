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
| `alembic/` | миграция `20261020_0001` |
| `tests/` | юнит/интеграция БД и аналитики |

## Установка и тесты

```sh
cd apps/api
python -m pip install -r requirements.txt
set PYTHONPATH=src
python -m pytest -q
```

SQLite in-memory используется в тестах (`create_all`). Для Postgres:

```sh
set DATABASE_URL=postgresql+psycopg2://synaptix:synaptix@localhost:5432/synaptix
set APP_ENV=demo
alembic upgrade head
python -c "from synaptix_api.db.session import SessionLocal; from synaptix_api.db.seed import seed_demo; db=SessionLocal(); print(seed_demo(db))"
```

Демо-пароль seed: `demo1234`.

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
