# Фактический статус GitHub

Проверка первичной настройки выполняется 2026-10-20. Итоговые результаты будут
записаны после push и чтения API. Желаемые JSON-профили не равны применённым правилам.

Репозиторий: https://github.com/2612evgenii-hue/synaptix-credit-cabinet
Видимость: private. Владелец: 2612evgenii-hue.

Повторная проверка: `python3 scripts/github_audit.py` (только чтение; JSON в
`artifacts/audit/github-settings.json`; ненулевой код при пробеле в защите/доступе).

## Применение профилей главным администратором

Команды меняют только настройки этого репозитория. Если правило уже существует,
сначала прочитать его и сравнить, а не перезаписывать неизвестные требования.

```sh
gh api --method PUT repos/2612evgenii-hue/synaptix-credit-cabinet/branches/main/protection --input config/github/main-protection.json
gh api --method POST repos/2612evgenii-hue/synaptix-credit-cabinet/rulesets --input config/github/tag-ruleset.json
python3 scripts/github_audit.py
```

При 403 из-за тарифа сохранить private и не считать локальный hook эквивалентом
серверной защиты. Варианты: GitHub Pro для личного private repo либо организация
с подходящим тарифом. Покупка/публичная публикация требуют отдельного решения владельца.
Настройки платного GitHub относятся к инструментам разработки, а не к зависимости
проверяемого прототипа от платного сервиса (условие кейса, страница 10).
