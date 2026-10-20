# Backend API (зона: данные, БД, аналитика риска)

Ответственный: **NamePantrer**. Issues: [#4](https://github.com/2612evgenii-hue/synaptix-credit-cabinet/issues/4) persistence/seed,
[#6](https://github.com/2612evgenii-hue/synaptix-credit-cabinet/issues/6) checks/risk/decision.

## Сейчас в ветке `feat/4-persistence-seed`

- ORM-модель по `docs/data-model.md` (`src/synaptix_api/models`)
- Alembic migration `20261020_0001`
- Идемпотентный demo-seed из `data/synthetic/scenarios.json`
- ADR-0002: PostgreSQL + SQLAlchemy

HTTP lifecycle и UI — следующие PR (Issues #5/#7). Пока сервер/compose не обязательны
для merge этого каркаса, но модели готовы к подключению FastAPI.

## Локально (после Compose с Postgres)

```sh
cd apps/api
python -m pip install -r requirements.txt
set PYTHONPATH=src
set DATABASE_URL=postgresql+psycopg2://synaptix:synaptix@localhost:5432/synaptix
set APP_ENV=demo
alembic upgrade head
python -c "from synaptix_api.db.session import SessionLocal; from synaptix_api.db.seed import seed_demo; db=SessionLocal(); seed_demo(db)"
```

Демо-пароль seed: `demo1234`. Логины: `client.approval@demo.local`,
`client.clarification@demo.local`, `client.rejection@demo.local`,
`bank.officer@demo.local`.
