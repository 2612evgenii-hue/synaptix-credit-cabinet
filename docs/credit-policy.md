# Учебная кредитная политика (demo-rules-v1)

Версия правил: `demo-rules-v1`. Реализация: `apply_decision_rules`.

## Порядок (приоритет сверху вниз)

| Порядок | Условие | outcome | reason_code |
| --- | --- | --- | --- |
| 1 | currency ≠ RUB | REJECTED | UNSUPPORTED_CURRENCY |
| 2 | нецелый/невалидный term/amount | REJECTED | INVALID_TERM_OR_AMOUNT |
| 3 | отрицательные деньги | REJECTED | NEGATIVE_MONEY_FIELDS |
| 4 | нет revenue/expenses/liabilities | NEEDS_INFO | INCOMPLETE_FINANCIALS |
| 5 | вне лимитов продукта | REJECTED | PRODUCT_LIMIT |
| 6 | registry negative | REJECTED | REGISTRY_NEGATIVE |
| 7 | bureau negative | REJECTED | BUREAU_NEGATIVE |
| 8 | bureau ok + overdue>0 | REJECTED | BUREAU_OVERDUE |
| 9 | unknown check status | NEEDS_INFO | CHECKS_INCOMPLETE |
| 10 | check unavailable | CHECK_UNAVAILABLE | CHECK_TECHNICAL_FAILURE |
| 11 | missing_data check | NEEDS_INFO | CHECKS_INCOMPLETE |
| 12 | score ≤ 35 | REJECTED | RISK_FLOOR |
| 13 | K ≥ 1.3 и score ≥ 55 | APPROVED | K_PASS, RISK_OK, CHECKS_OK |
| 14 | есть alt в лимитах | ALTERNATIVE | ALTERNATIVE_AMOUNT |
| 15 | иначе | REJECTED | COVERAGE_OR_RISK_FAIL |

**Нельзя:** подменять null нулём; трактовать unavailable как отказ; менять outcome через LLM.

Сообщения для UI строятся из reason_codes (`explain.py` / шаблоны).
