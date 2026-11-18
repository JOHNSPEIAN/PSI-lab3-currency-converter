# Публикация на GitHub и Pull Request

Агент подготовил все ветки локально, но создать репозиторий на GitHub и открыть Pull Request
не может: на компьютере нет `gh`, а для GitHub нужна авторизация владельца аккаунта.
Ниже — точные шаги и готовые тексты PR.

## 1. Репозиторий и отправка веток

1. На github.com → **New repository** → имя `PSI-lab3-currency-converter`, **без** README,
   .gitignore и лицензии.
2. В папке проекта:

```powershell
git remote add origin https://github.com/JOHNSPEIAN/PSI-lab3-currency-converter.git
git push -u origin main
git push -u origin spec/currency-converter feature/implementation test/unit-tests docs/report
```

3. (Рекомендуется) Settings → Branches → Add rule для `main` → «Require a pull request before
   merging». Тогда прямой push в `main` будет невозможен.

## 2. Порядок PR

PR сливаются **строго по порядку**, каждый — кнопкой **Create a merge commit** (не Squash и не
Rebase, иначе пропадёт история шагов). Ветки идут цепочкой, поэтому после слияния предыдущего PR
в следующем останутся только его собственные коммиты.

| № | Из ветки | В ветку | Заголовок |
|---|---|---|---|
| 1 | `spec/currency-converter` | `main` | Specs: currency converter — constitution, spec, plan, tasks, analysis |
| 2 | `feature/implementation` | `main` | Implementation: currency converter with local web GUI |
| 3 | `test/unit-tests` | `main` | Tests: 186 network-free unit tests |
| 4 | `docs/report` | `main` | Docs: lab report and pull request notes |

Тексты описаний лежат также отдельными файлами в `docs/pr/` — их удобно вставлять в поле описания PR.

С GitHub CLI (если установите `gh` и выполните `gh auth login`):

```powershell
gh pr create --base main --head spec/currency-converter --title "Specs: currency converter — constitution, spec, plan, tasks, analysis" --body-file docs/pr/01-specs.md
gh pr merge spec/currency-converter --merge
gh pr create --base main --head feature/implementation --title "Implementation: currency converter with local web GUI" --body-file docs/pr/02-implementation.md
gh pr merge feature/implementation --merge
gh pr create --base main --head test/unit-tests --title "Tests: 186 network-free unit tests" --body-file docs/pr/03-tests.md
gh pr merge test/unit-tests --merge
gh pr create --base main --head docs/report --title "Docs: lab report and pull request notes" --body-file docs/pr/04-report.md
gh pr merge docs/report --merge
```

---

## PR 1 · Specs: currency converter — constitution, spec, plan, tasks, analysis

**EN.** Spec Kit artifacts only, no application code.
- Constitution v1.0.0: GUI first, SOLID (non-negotiable), never crash, offline with honest
  provenance, Decimal money, network-free tests, minimal dependencies, bilingual commits.
- `specs/001-currency-converter`: spec (4 user stories, 20 FRs, 6 SCs) with clarifications, plan,
  research (real BNM behaviour), data model, API/UI contracts, quickstart, 53 tasks in 8 phases,
  `/speckit-analyze` report (0 critical) and the fixes it suggested.

**RU.** Только артефакты Spec Kit, кода приложения нет.
- Конституция v1.0.0: приоритет GUI, SOLID (обязательно), приложение не падает, офлайн с честным
  указанием источника, деньги на Decimal, тесты без сети, минимум зависимостей, двуязычные коммиты.
- `specs/001-currency-converter`: спецификация (4 сценария, 20 FR, 6 SC) с уточнениями, план,
  исследование (реальное поведение НБМ), модель данных, контракты API и UI, quickstart, 53 задачи в
  8 фазах, отчёт `/speckit-analyze` (0 критических) и правки по нему.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

---

## PR 2 · Implementation: currency converter with local web GUI

**EN.** Phases 1–7 of `tasks.md`.
- Layered SOLID package: domain (Decimal converter, validation, calendar), Protocol ports, adapters
  (BNM XML, urllib, JSON saved copy, memo decorator, browser launcher), presentation, web API.
- Glass-style responsive UI with light/dark themes, searchable currency pickers, offline mode,
  weekend/holiday notices.
- Fix: BNM answers unpublished dates with 404 (research corrected).
- README, Russian operating manual, screenshots, `run.bat`. Quickstart V1–V12 checked manually.

**RU.** Фазы 1–7 из `tasks.md`.
- Слоистый пакет по SOLID: домен (конвертер на Decimal, проверка ввода, календарь), порты на
  Protocol, адаптеры (XML НБМ, urllib, JSON-копия, декоратор-кэш, запуск браузера), представление,
  веб-API.
- Адаптивный «стеклянный» интерфейс со светлой и тёмной темами, поиском валют, офлайн-режимом и
  уведомлениями о выходных и праздниках.
- Исправление: НБМ отвечает на неопубликованные даты кодом 404 (исследование исправлено).
- README, инструкция по эксплуатации, скриншоты, `run.bat`. Сценарии V1–V12 проверены вручную.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

---

## PR 3 · Tests: 186 network-free unit tests

**EN.** Phase 8 of `tasks.md`. `python -m pytest` → 186 passed in ~3 s without internet.
Covers BNM parsing (recorded real answers and broken variants), conversion both ways, empty/malformed
source answers, input validation, fallback rules, offline mode, saved copy on disk, presentation and
the JSON API. A test found a bug (invalid source URL → HTTP 500), fixed in `fix(http)`; another test
documents a limit of SC-004.

**RU.** Фаза 8 из `tasks.md`. `python -m pytest` → 186 тестов за ~3 с без интернета. Покрыты разбор
ответа НБМ (реальные записанные ответы и сломанные варианты), конвертация в обе стороны,
пустые/некорректные ответы источника, проверка ввода, правила отката по датам, офлайн-режим,
сохранённая копия на диске, представление и JSON API. Один тест нашёл баг (неверный адрес источника
→ HTTP 500), исправлен в `fix(http)`; другой тест фиксирует ограничение SC-004.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

---

## PR 4 · Docs: lab report and pull request notes

**EN.** `REPORT.md` (data source choice, tools and models actually used, what worked first time,
agent errors and fixes, spec compliance, git process, conclusions) and these PR notes.

**RU.** `REPORT.md` (выбор источника данных, реально использованные инструменты и модели, что
получилось с первой попытки, ошибки агента и исправления, соответствие спецификации, работа с git,
выводы) и эти заметки о PR.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
