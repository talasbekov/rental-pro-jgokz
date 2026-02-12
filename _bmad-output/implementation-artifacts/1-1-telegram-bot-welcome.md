# Story 1.1: Запуск Telegram-бота и welcome-сценарий

Status: done

**Story Key:** `1-1-telegram-bot-welcome`  
**Epic:** 1 — Первое касание и знакомство с продуктом  
**Дата контекстирования:** 2026-02-09  

**Коротко:** реализовать русский welcome-сценарий в Telegram-боте: при `/start` показать приветствие + кнопку «Попробовать поиск», без регистрации; Telegram `user_id` сохраняется автоматически (silent auth уже реализован middleware).  

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a гость,
I want нажать `/start` и сразу увидеть приветствие с демо-поиском,
so that за 30 секунд понять, что это за сервис и какие квартиры доступны.

## Acceptance Criteria

1. **Given** пользователь нажимает `/start` в Telegram  
   **When** бот обрабатывает команду  
   **Then** бот отправляет **одно** welcome‑сообщение **на русском языке** (FR9) с кратким описанием сервиса и **одним** основным CTA: inline‑кнопка «Попробовать поиск».
2. **And** welcome‑сообщение предлагает “лучший путь” через текстовый ввод (пример запроса внутри сообщения).
3. **And** бот **не** запрашивает регистрацию, телефон/email, документы, согласия или любые формы ввода данных в рамках welcome‑сценария.
4. **And** silent auth выполняется автоматически: пользователь в БД создаётся/находится по `message.from_user.id` через существующий `AuthMiddleware`, без дополнительных действий пользователя.
5. **When** пользователь нажимает «Попробовать поиск»  
   **Then** бот делает `callback_query.answer()` и запускает следующий шаг onboarding-пути поиска (в текущей версии — demo preview из Story 1.2), сохраняя короткие RU-подсказки и без дополнительных форм/регистрации.
6. **And** сценарий совместим со Story 1.2: пользователь может либо нажать «Попробовать поиск», либо просто написать запрос в чат.
7. **And** сообщения должны быть короткими (1–3 строки + пример) и не содержать “технических” терминов.
8. **Non-goals (на момент первоначальной реализации Story 1.1):** поиск/карточки/structured-flow меню/мини‑апп были вне scope этой story; фактическая реализация расширена в последующей Story 1.2.
9. **And** обработчик кнопки устойчив к вариантам update: если `callback_query.message` отсутствует, бот всё равно делает `callback_query.answer()` и отправляет подсказку через `bot.send_message(callback_query.from_user.id, ...)`.
10. **And** повторные действия не приводят к странному UX:
   - повторный `/start` возвращает актуальный welcome (без ошибок/исключений);
   - повторный клик по «Попробовать поиск» снова отдаёт подсказку (или мягко говорит “напишите запрос”), без “вечной загрузки”.
11. **And** ошибки на стороне бота/БД не приводят к молчанию: при исключении обработчик всё равно отвечает пользователю (минимум — короткий fail‑soft текст + инструкция попробовать ещё раз или `/start`).

## Tasks / Subtasks

- [x] **Task 1: `/start` welcome** (AC: #1-4)
  - [x] Обновить `backend/bot/handlers/start.py`: русский текст + inline‑кнопка «Попробовать поиск».
  - [x] Зафиксировать тексты в коде (пока без i18n), без длинных полотен.
  - [x] Текст welcome (предлагаемый):
    - «Привет! Помогу найти квартиру посуточно.  
      Нажми кнопку ниже или напиши запрос (например: “квартира в центре на завтра до 15000₸”).»
- [x] **Task 2: Callback «Попробовать поиск»** (AC: #5-6)
  - [x] Добавить handler на `callback_query` с `callback_data="try_search"` (коротко).
  - [x] В handler: `await callback_query.answer()` и `await callback_query.message.answer(<подсказка+пример>)`.
  - [x] Текст после кнопки (предлагаемый):
    - «Отлично — напиши, что ищешь: район/даты/бюджет.  
      Пример: “1 комната в центре на завтра до 15000₸”.»
  - [x] Учесть `callback_query.message is None` → отправка через `bot.send_message(...)`.
  - [x] Повторный клик: всегда `callback_query.answer()` + повтор подсказки (без “вечной загрузки”).
- [x] **Task 3: Проверка UX/функционала** (AC: #1-7)
  - [x] Ручная проверка: `/start` → welcome+кнопка; клик → мгновенный ответ + подсказка; `/help` и fallback не ломаются.
  - [x] (Опционально) если в проекте уже есть паттерн тестов для aiogram handlers — добавить минимальный тест на формирование inline keyboard и на тексты.
  - [x] Definition of Done (Story 1.1):
    - [x] `/start` всегда отдаёт RU welcome + кнопку (без дублей/спама).
    - [x] Кнопка всегда “откликается” (есть `callback_query.answer()`).
    - [x] Никаких запросов регистрации/данных.
    - [x] Код-структура соответствует границам: `bot/` — тонкий слой; бизнес‑логика не уезжает в `bot/`.
  - [x] Ручная матрица проверок:
    - [x] `/start` (private chat)
    - [x] `/start` повторно
    - [x] клик по «Попробовать поиск»
    - [x] клик по кнопке повторно
    - [x] сценарий “callback без message” (если не воспроизводится — оставить защитный код)
  - [x] Проверить fail‑soft: при исключении в middleware/DB бот отвечает пользователю (и пишет лог).

## Dev Notes

- **Где менять:** `backend/bot/handlers/start.py` (сейчас англ. текст), добавить callback handler в `backend/bot/handlers/` (отдельным файлом или рядом).
- **Silent auth:** `backend/bot/middlewares/auth.py` уже делает find-or-create по Telegram ID и кладёт `data["db_user"]`; в welcome не добавлять отдельную “регистрацию”.
- **Важно для Telegram UX:** всегда отвечать `callback_query.answer()`, иначе у пользователя висит “loading”.
- ParseMode в боте — HTML (`backend/bot/main.py`), поэтому в текстах либо не использовать разметку, либо внимательно избегать случайных HTML-тегов.
- В callback handler делай `callback_query.answer()` до любых операций и не предполагай, что `callback_query.message` всегда есть.
- На ошибках — **fail-soft**: отвечай пользователю коротким сообщением, не оставляй без реакции.

### Developer Context

- **Текущее приложение бота:** `backend/bot/main.py` — aiogram 3 + `aiohttp`, webhook endpoint `/webhook`, проверка `secret_token`.
- **Слои и границы:** `bot/` должен оставаться тонкой UX-обвязкой; доступ к БД/бизнес‑логике — через `backend/shared/` (уже так сделано для пользователей).
- **Текущие обработчики:** `backend/bot/handlers/start.py` и `backend/bot/handlers/common.py` подключаются в `backend/bot/main.py`.
- **Рекомендуемая структура для Story 1.1:** добавить новый handler-файл (например, `backend/bot/handlers/welcome.py`) для callback `try_search` и подключить его router рядом со `start.router`.

### Technical Requirements

- **Команды/триггеры:**
  - `/start` (CommandStart) → welcome + inline‑кнопка «Попробовать поиск».
  - Callback `try_search` → `callback_query.answer()` + подсказка “введите текстовый запрос”.
- **Inline‑клавиатура:** использовать inline‑кнопку (а не reply keyboard), чтобы CTA был “внутри” сообщения и не раздувал меню.
- **Callback UX:** всегда вызывать `callback_query.answer()`; если `callback_query.message` отсутствует — отправлять подсказку через `bot.send_message(callback_query.from_user.id, ...)`.
- **Отсутствие побочных эффектов:** не добавлять новые `.env` переменные и не менять webhook/маршрутизацию; не выполнять тяжёлых запросов/интеграций в обработчиках welcome.
- **Язык:** весь UX‑текст строго на русском (FR9).

### File Structure Requirements

- **Изменить:** `backend/bot/handlers/start.py`
  - RU welcome‑текст
  - Inline keyboard с кнопкой «Попробовать поиск» (`callback_data="try_search"`)
- **Добавить:** `backend/bot/handlers/welcome.py`
  - `Router()`
  - handler на callback `try_search`
  - `callback_query.answer()` + отправка подсказки/примера (fail‑soft, в т.ч. когда `callback_query.message is None`)
- **Изменить:** `backend/bot/main.py`
  - импортировать `welcome` рядом с `start/common`
  - `dp.include_router(welcome.router)` (чтобы кнопка не “молчала”)
- **Не трогать в этой Story:** `backend/shared/*`, `backend/app/*`, `compose*.yml`, `.env` (нет новых переменных/сервисов).

### Testing Requirements

- **Минимум для Story 1.1:** ручная проверка по матрице из Tasks (включая повторный `/start`, повторный клик, fail‑soft).
- **Автотесты (опционально):**
  - В проекте сейчас нет явного `aiogram.testing` паттерна в `backend/tests/`; если не хотите тащить новый инструментарий — ограничиться ручной матрицей.
  - Если всё же добавлять тесты, держать их “тонкими”: проверка, что inline‑клавиатура содержит кнопку с `callback_data="try_search"`, и что handler вызывает `callback_query.answer()` (можно через мок объекта callback).

### Project Structure Notes

- [TBD]

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Story 1.1`]
- [Source: `_bmad-output/planning-artifacts/epics.md#Story 1.2`]
- [Source: `_bmad-output/planning-artifacts/prd.md#FR9`]
- [Source: `_bmad-output/planning-artifacts/prd.md#FR8`]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` (guided first experience)]
- [Source: `backend/bot/handlers/start.py`]
- [Source: `backend/bot/middlewares/auth.py`]
- [Source: `backend/bot/main.py`]

## Senior Developer Review (AI)

### Review Date

2026-02-09

### Outcome

Changes Requested → Fixed

### Findings Summary

- High: 1
- Medium: 3
- Low: 0

### Findings

- [x] [HIGH] В user-facing help/fallback остались английские тексты (`backend/bot/handlers/common.py`).
- [x] [MEDIUM] Глобальный fail-soft покрывал не все типы update (`backend/bot/main.py`).
- [x] [MEDIUM] Формат логирования исключения в `on_error` не гарантировал корректный traceback (`backend/bot/main.py`).
- [x] [MEDIUM] Не хватало тестов для fail-soft на уровне `on_error` (`backend/bot/tests/test_main_error_handler.py`).

### Follow-up Review Date

2026-02-10

### Follow-up Outcome

Changes Requested → Fixed

### Follow-up Findings Summary

- High: 2
- Medium: 4
- Low: 0

### Follow-up Findings

- [x] [HIGH] AC5 противоречил фактическому поведению после Story 1.2 (`try_search` ведёт в demo preview).
- [x] [HIGH] Non-goals секция не отражала post-story эволюцию функциональности.
- [x] [MEDIUM] Описание Task 2 (подсказка-only) не соответствовало текущему интеграционному контракту.
- [x] [MEDIUM] Тестовый контракт `test_welcome_handlers.py` проверял demo preview, что не было явно отражено в тексте story.
- [x] [MEDIUM] File List требовал синхронизации с фактической связкой welcome + search.
- [x] [MEDIUM] Нужна явная фиксация того, что поведение Story 1.1 расширено последующей Story 1.2.

## Dev Agent Record

### Agent Model Used

GPT-5.2 (Codex CLI)

### Debug Log References

- `./.venv/bin/python -m pytest -q backend/bot/tests`
- `./.venv/bin/python -m ruff check backend/bot`

### Completion Notes List

- Ultimate context engine analysis completed — comprehensive developer guide created
  - Determined minimal scope: welcome + try_search hint (no search/cards yet)
  - Defined file-level changes (`start.py`, new `welcome.py`, `main.py` include_router)
  - Added UX guardrails (RU only, short messages, fail-soft)
- Implemented RU `/start` welcome + inline button `try_search`
- Added `try_search` callback handler (always `callback_query.answer()`, supports missing `callback_query.message`)
- `try_search` интегрирован с demo preview потоком (расширение scope выполнено в рамках Story 1.2)
- Added global fail-soft error handler to avoid silent failures (including middleware/DB exceptions)
- Added unit tests for handlers and kept lint green (`ruff`)
- Verified: `backend/bot/tests` pass and `ruff` passes
- Code-review autofix applied:
  - `help` и fallback переведены на русский
  - `on_error` расширен для `edited_message`, `channel_post`, `edited_channel_post`
  - logging в `on_error` скорректирован для передачи исключения
  - добавлены unit-тесты `test_main_error_handler.py`

### File List

- `_bmad-output/implementation-artifacts/1-1-telegram-bot-welcome.md` (story updates)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (story status)
- `backend/bot/handlers/start.py` (RU welcome + CTA button)
- `backend/bot/handlers/common.py` (RU help/fallback texts)
- `backend/bot/handlers/welcome.py` (callback handler)
- `backend/bot/handlers/search.py` (demo preview integration for `try_search`)
- `backend/bot/main.py` (router include + fail-soft error handler)
- `backend/bot/tests/test_welcome_handlers.py` (unit tests)
- `backend/bot/tests/test_search_handler.py` (search flow unit tests used by current `try_search` path)
- `backend/bot/tests/test_main_error_handler.py` (error handler unit tests)

## Change Log

- 2026-02-09: RU welcome + try_search callback (+ fail-soft error handling + unit tests).
- 2026-02-09: Code-review autofix: RU help/fallback + improved global on_error + extra fail-soft tests.
- 2026-02-10: Story text aligned with actual integrated behavior after Story 1.2; follow-up review findings closed.
