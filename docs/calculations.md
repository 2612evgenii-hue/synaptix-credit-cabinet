# Учебные расчёты (демо)

Все пороги и ставка — **учебные**, не политика Альфа-Банка.

## Доступный поток

`available = revenue_minor - expenses_minor` (месячные величины за `period_label`, демо: один месяц).  
Если `revenue` или `expenses` = null → поток неизвестен → `NEEDS_INFO`.  
`null ≠ 0`. Поле `liabilities_minor` — остаток обязательств (не месячный платёж).

## Аннуитет (месяц)

```
i = demo_rate_annual / 12
A = S * i / (1 - (1+i)^(-n))   если i > 0
A = S / n                        если i = 0
```

S — сумма в копейках, n — месяцы, A — округление до целых копеек (`round`).

Демо-ставка по умолчанию: `0.16` годовых.

## Покрытие K

```
K = available / (existing_debt_payment + new_payment)
```

В текущем демо `existing_debt_payment = 0` (упрощение D10). Поле `FinancialSnapshot.debt_service_monthly_minor` сохраняет явный месячный платёж по старым долгам для API/UI; движок пока не подставляет его в K, пока интегратор не передаст значение. `liabilities_minor` — остаток обязательств, учитывается в risk (leverage), не как месячный платёж.  
Порог одобрения: `K_PASS = 1.3`. Сравнение идёт по **точному** K (без round-up в порог).

## Альтернатива

Если полный запрос не проходит K, ищется max principal с `K >= K_PASS` в лимитах продукта (сетка 10 000 ₽, с сохранением `product_min`).

Эталонная реализация: `apps/api/src/synaptix_api/analytics/decision.py`.
