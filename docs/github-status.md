# Статус и проверка GitHub

Репозиторий: https://github.com/2612evgenii-hue/synaptix-credit-cabinet

| Область | Настройка / источник фактического результата |
| --- | --- |
| Видимость | **public**, явно выбрано владельцем 2026-10-20 |
| Главный администратор | 2612evgenii-hue, владелец личного репозитория |
| NamePantrer | Приглашён с write, на первичной проверке ожидал принятия |
| SergeEvdokimov | Приглашён с write, на первичной проверке ожидал принятия |
| Merge | Только squash; автоматическое удаление рабочей ветки; auto-merge выключен |
| main | Профиль config/github/main-protection.json; итог активации и проверки в Issue #1 |
| Теги v* | Неизменяемость без bypass; отдельное правило создания только admin |
| CI | repository-policy и secret-scan, GitHub Actions, минимальный read token |
| Issues | 12 начальных задач, P0/P1, 3 milestones; распределение работы ещё согласовать |
| Доступ жюри | Чтение public repo без приглашения; проверить точную ссылку сдачи |

GitHub отклонил защиту private repo с HTTP 403. После выбора владельцем public
это ограничение устранено. Публичность не предоставляет автоматически лицензию
на использование кода; решение о лицензии команда ещё не приняла.

Документ фиксирует bootstrap. Текущее состояние проверяет
`python3 scripts/github_audit.py`: это только чтение, JSON записывается в
`artifacts/audit/github-settings.json`. Ненулевой код показывает пробелы в защите
или непринятые приглашения. Исправная защита и принятое приглашение — разные проверки.
Проверка 2FA личных аккаунтов не доступна этому скрипту.

[Issue #1: результаты активации и проверки защиты](https://github.com/2612evgenii-hue/synaptix-credit-cabinet/issues/1).
[История CI](https://github.com/2612evgenii-hue/synaptix-credit-cabinet/actions).

## Повторное применение администратором

Профили не применяются фоновым процессом и не меняют настройки сами.
Для нового окружения сначала прочитать действующие правила и сравнить:

```sh
gh api repos/2612evgenii-hue/synaptix-credit-cabinet/branches/main/protection
gh api repos/2612evgenii-hue/synaptix-credit-cabinet/rulesets
# PUT обновляет main profile; POST создаёт НОВОЕ правило — не дублировать существующее.
gh api --method PUT repos/2612evgenii-hue/synaptix-credit-cabinet/branches/main/protection --input config/github/main-protection.json
# Для отсутствующих tag rulesets:
gh api --method POST repos/2612evgenii-hue/synaptix-credit-cabinet/rulesets --input config/github/tag-ruleset.json
gh api --method POST repos/2612evgenii-hue/synaptix-credit-cabinet/rulesets --input config/github/tag-creation-ruleset.json
python3 scripts/github_audit.py
```

Администратор технически может изменять настройки репозитория. Правила GitHub
не защищают от владельца, намеренно отключившего их. Для контроля таких изменений
используются журнал решений и независимые экспорты состояния.
