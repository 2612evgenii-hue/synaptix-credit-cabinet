# Словарь данных (зона аналитики / БД)

Статус: рабочий для `apps/api` ORM. Деньги в продукте — **целые копейки** (`*_minor`).
В AI-контракте сумма дополнительно дублируется строкой рублей (`amount_rub`) для UI.

| Поле | Сущность | Тип | Ед. | Null? | Смысл |
| --- | --- | --- | --- | --- | --- |
| synthetic_registration_id | Company | string | — | no | Синтетический рег. id |
| scenario_key | Company | string | — | yes | Ключ демо-сценария |
| demo_login | User | string | — | no | Логин демо |
| role | User | enum | — | no | customer / bank |
| code | Product | string | — | no | working_capital / equipment |
| min/max_amount_minor | Product | int | коп. | no | Лимиты суммы |
| min/max_term_months | Product | int | мес. | no | Лимиты срока |
| amount_minor | Application | int | коп. | yes | Запрошенная сумма |
| term_months | Application | int | мес. | yes | Срок |
| revenue_minor | FinancialSnapshot | int | коп./период | yes | Выручка; null ≠ 0 |
| expenses_minor | FinancialSnapshot | int | коп./период | yes | Расходы |
| liabilities_minor | FinancialSnapshot | int | коп. | yes | Обязательства |
| status | CheckResult.result | enum | — | no | ok / negative / unavailable / missing_data |
| overdue_days | CheckResult payload | int | дни | — | Просрочка бюро |
| score | RiskAssessment | int | 0..100 | no | Риск, не решение |
| outcome | Decision | enum | — | no | APPROVED / … |
| reason_codes | Decision | list | — | no | Машинные причины |
| explanation_* | Decision | text | — | yes | Пост-hoc объяснение |
| llm_meta | Decision | json | — | no | backend/model/fallback |

**Инварианты:** `null` = неизвестно; `0` = известный ноль; срок — целые месяцы; валюта MVP — RUB.
