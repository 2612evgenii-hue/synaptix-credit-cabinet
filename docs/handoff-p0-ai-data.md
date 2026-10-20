# Handoff: P0 AI / data / analytics (NamePantrer)

**Branch:** `feat/p0-ai-data-integration`  
**Base:** `93f7456` (PR №15)  
**Date:** 2026-10-20

## Packages delivered

| ID | Deliverable |
| --- | --- |
| AI01 | ENUM `create_type=False`; migration `20261020_0004` (decision↔snapshot, catalog columns, debt_service/period); `docker-compose.postgres-verify.yml` + `scripts/verify_postgres_ai01.py` |
| AI02 | Catalog from `data/products.json`; decision snapshot/product/version binding; `contracts/examples/decision-outcomes.json`; D10 debt_service documented |
| AI03 | `ru-heuristic-v2` extract; QA A01–A10 = 10/10 amount+term; D01/D04 fixed; `data/qa/extract-phrases.json` + `tests/test_extract_qa_phrases.py` |
| AI04 | Expanded `ai-extract.output.schema.json` + examples (ok/incomplete/ambiguous/model-off/model-error) |
| DATA01 | 17 synthetic scenarios + expected-results; mocks for new keys |

## Commands

```powershell
cd apps/api
$env:PYTHONPATH="src"
$env:LLM_BACKEND="template"
$env:APP_ENV="demo"
py -3 -m pytest -q
py -3 -m pytest tests/test_extract_qa_phrases.py -q

# PostgreSQL AI01 (requires Docker Desktop running):
docker compose -f docker-compose.postgres-verify.yml up -d
$env:DATABASE_URL="postgresql+psycopg2://synaptix:synaptix@127.0.0.1:54329/synaptix_verify"
py -3 scripts/verify_postgres_ai01.py --write-log
docker compose -f docker-compose.postgres-verify.yml down -v
```

## Integrator notes (Evgeny)

- Extract never writes applications; always `needs_user_confirm=true`.
- Canonical money: `amount_minor` (kopecks) + matching `amount_rub` string.
- Outcomes `ALTERNATIVE` / `CHECK_UNAVAILABLE` exist in analytics contracts; map explicitly in OpenAPI/state machine (D09).
- Seed is idempotent and must not delete user-created demo applications.
- Product catalog source of truth: `data/products.json` (seed syncs ORM extras).

## Migration rollback policy

- Forward: `alembic upgrade head` (0001→0004).
- Downgrade 0004 drops added columns (safe).
- ENUM types in 0001 are created with `checkfirst=True`; downgrade drops them. Re-adding enum values later is irreversible without restore — prefer restore from backup over partial enum surgery.

## Remaining limits

- Real Ollama hardware run / checksum (AI05–AI06) is P1.
- Soft LLM merge still heuristic-owned (D06 intentional until AI06).
- Product Compose owned by Evgeny; verify compose is temporary.
- Full 30-phrase QA report for Serge: run `data/qa/extract-phrases.json` plus remaining rows in `docs/qa/ai-phrases.md`.
