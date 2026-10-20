# Аудит зоны «данные и аналитика» (NamePantrer)

Дата: 2026-10-20. Ветка: `feat/4-persistence-seed`. Scope: БД + риск/решение/моки/seed.  
Вне аудита: HTTP API, веб, Compose web (другие зоны команды).

## Вердикт

**Зона функционально закрыта.** Модель данных, Alembic, idempotent demo-seed,
детерминированный pipeline `mocks → risk → decision → persist`, и полный набор
регрессионных + adversarial-тестов на месте. HTTP-слой сознательно не реализован.

Финальный прогон: **`78 passed`** (`py -3 -m pytest -q` в `apps/api`).  
Adversarial: циклы 1–12 с багами (все закрыты фикcами + тестами), **цикл 13: NO NEW FINDINGS**.

## Покрытие требований зоны

| REQ / Issue | Статус |
| --- | --- |
| #4 модель + миграции + seed | Готово (Alembic + ORM + idempotent seed с repair) |
| #6 risk отдельно от decision + моки | Готово (`analytics/`) |
| REQ-07/12/17 синтетика | Seed + `data/synthetic/scenarios.json` |
| REQ-16 локальные моки | `mocks.py` (детерминированный `checked_at`) |
| REQ-22 упрощения описаны | ADR-0002, reason_codes, metrics |
| Score ≠ decision | `assess_risk` vs `apply_decision_rules` |
| unavailable ≠ reject | `CHECK_UNAVAILABLE` / `CHECK_TECHNICAL_FAILURE` |
| None ≠ 0 | `NEEDS_INFO` / `INCOMPLETE_FINANCIALS` / `missing_cashflow` |
| Hard deny ≻ soft peer | Negative/overdue не маскируются unavailable/missing_data |

## Артефакты

| Путь | Назначение |
| --- | --- |
| `apps/api/src/synaptix_api/models` | ORM / data-model |
| `apps/api/alembic/versions/20261020_0001_initial_schema.py` | PostgreSQL schema |
| `apps/api/src/synaptix_api/db/seed.py` | Demo seed + identity/catalog repair |
| `apps/api/src/synaptix_api/db/passwords.py` | Hash/verify без raise на corrupt hash |
| `apps/api/src/synaptix_api/analytics/*` | mocks, risk, decision, pipeline, persist |
| `apps/api/tests` + `tests/adversarial` | Unit + 13 циклов adversarial |
| `apps/api/tests/adversarial/FINDINGS.md` | Журнал атак |

## Инварианты, зафиксированные adversarial-циклами

1. **K / decision:** `K_PASS` не лжёт; border-k не APPROVE; ALTERNATIVE не обходит RISK_FLOOR.
2. **Checks:** `missing_data` / unknown status → NEEDS_INFO; `unavailable` → CHECK_UNAVAILABLE; hard `negative`/`overdue` не смягчаются soft peer-check.
3. **Bureau overdue:** `ok`+overdue>0 → REJECT; negative/fractional/malformed overdue не APPROVE; explicit `negative` не маскируется malformed overdue.
4. **Money/term:** строгие int (не float/string); currency RUB; negative money / invalid term → REJECT.
5. **Mocks:** детерминированный `checked_at`; bureau без `status` → `missing_data`; registry soft/unknown/incomplete не invent `REGISTRY_NEGATIVE`; `found="false"` не truthy.
6. **Seed:** полнота по officer+products+scenario companies/customers; repair role/password/`company_id`/limits; corrupt `password_hash` → False verify → repair, без crash.
7. **Persist / model:** ApplicationState покрывает ALTERNATIVE/CHECK_UNAVAILABLE; metrics не гнездятся ломающе; check status не затирается payload entity status.

## Риски / долг (не блокеры зоны)

1. Alembic под PostgreSQL UUID/Enum; unit-тесты — SQLite `create_all`.
2. Compose БД — Issue #9 (infra), вне зоны.
3. Сценарий `bureau_down` в моках, не в seed `scenarios.json` (опционально).
4. ADR-0002 ждёт approve команды (#3).
5. Case-variant adverse registry (`LIQUIDATING`) сейчас soft → NEEDS_INFO, не hard reject — осознанный trade-off (нет false APPROVE мёртвой компании в canonical lowercase).

## Рекомендация

Готово к использованию API-командой как библиотека: `run_analytics` + `persist.*`
без дублирования формул. Draft PR #15 — merge после owner-ревью зоны.
