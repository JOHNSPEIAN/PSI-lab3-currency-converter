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
