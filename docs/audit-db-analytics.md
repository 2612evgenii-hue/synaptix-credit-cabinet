# Аудит зоны «данные и аналитика» (NamePantrer)

Дата: 2026-10-20. Ветка: `feat/4-persistence-seed`.  
Scope: БД + риск/решение/моки/seed + **open-weight LLM explanations** (REQ-20).  
Вне аудита: HTTP API, веб, Compose web.

## Вердикт

**Зона функционально закрыта**, включая пост-hoc объяснения решений.

Финальный прогон: **`128 passed`** (`py -3 -m pytest -q` в `apps/api`).  
Adversarial: циклы 1–13 (БД/решение) + **A1–A5** (LLM/explain + K-rounding) закрыты фикcами;  
**цикл A6: NO NEW FINDINGS** (CLEAN).

## LLM (REQ-20)

| Элемент | Статус |
| --- | --- |
| Open weights only | Ollama-compatible local runtime; TinyLlama рекомендован |
| Default review build | `LLM_BACKEND=template` — без скачивания модели |
| Paid/cloud API | Blocked (short host, `.local`, hyphen compounds) |
| Credit path independence | LLM не меняет `DecisionResult.outcome`; fallback → template |
| Persist | `explanation_client` / `explanation_bank` / `llm_meta` на `decisions` |
| Migration | `20261020_0003_decision_explanations` |

## Покрытие требований зоны

| REQ / Issue | Статус |
| --- | --- |
| #4 модель + миграции + seed | Готово |
| #6 risk отдельно от decision + моки | Готово |
| REQ-20 open-weight LLM | Готово (`analytics/explain.py`) |
| Score ≠ decision | Держится |
| unavailable ≠ reject | Держится |
| None ≠ 0 | Держится |

## Артефакты

| Путь | Назначение |
| --- | --- |
| `analytics/explain.py` | template + Ollama explain, validation, host allowlist |
| `analytics/{mocks,risk,decision,pipeline,persist}.py` | конвейер |
| `db/seed.py`, `db/passwords.py` | demo seed + repair |
| `tests/` + `tests/adversarial/` | 128 тестов; FINDINGS.md |
| `docs/audit-db-analytics.md` | этот отчёт |

## Adversarial LLM (A1–A6)

Закрыто: contradictory/cross-outcome/negated cues; injection; paid hosts
(short / `.local` / hyphen); alt 10k-floor erase; K `round(...,4)` false approve.

## Долг (не блокеры)

Compose с Ollama опционален (infra); веса не вендорятся в репо; ADR-0002 approve.
