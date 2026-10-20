# ADR-0002: PostgreSQL + SQLAlchemy для persistence MVP

Дата: 2026-10-20. Статус: предложено зоной «данные и БД» (NamePantrer), ожидает
подтверждения команды в Issue #3 / ревью этого PR.

## Контекст

Нужны миграции, синтетический seed, сохранение заявок после рестарта Docker и
аудит событий (REQ-05/07/12/17, Issue #4). Стек продукта ещё не был зафиксирован.

## Решение

| Слой | Выбор | Версии (стартовые) |
| --- | --- | --- |
| БД | PostgreSQL 16 | образ `postgres:16-alpine` |
| ORM | SQLAlchemy 2.x | pin в `apps/api/requirements.txt` |
| Миграции | Alembic | pin рядом |
| Деньги | `BIGINT` копейки (`*_minor`) | без float |
| Время | UTC `TIMESTAMPTZ` | |
| Демо-сид | идемпотентный Python seed | только `APP_ENV=demo` |

Аналитика риска (`RiskAssessment`) и кредитное решение (`Decision`) — отдельные
таблицы: score ≠ outcome (см. architecture / Issue #6).

## Последствия

- Compose volume сохраняет данные между рестартами.
- Lock-файл `requirements.txt` (+ позже `uv.lock` / `pip-compile` по согласованию).
- SQLite допустим только для локальных unit-тестов без Docker, не для демо жюри.

## Отвергнуто сейчас

- Отдельная аналитическая OLAP-БД (избыточно для MVP).
- Обучение ML-модели на прод-данных (запрещено кейсом / нет реальных данных).
