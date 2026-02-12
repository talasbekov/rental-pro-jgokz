# Story 1.4: Базовая навигация через structured flow

Status: ready-for-dev

**Story Key:** `1-4-basic-navigation-structured-flow`
**Epic:** 1 — Первое касание и знакомство с продуктом
**Дата контекстирования:** 2026-02-10

**Коротко:** Реализовать базовую навигацию через кнопочное меню в Telegram-боте с главным меню (Поиск / Мои бронирования / Помощь) и кнопкой "Назад" на каждом уровне. Запросить согласие на обработку ПД при первом значимом действии.

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a гость,
I want пользоваться кнопочным меню для навигации (Поиск / Мои бронирования / Помощь),
so that легко ориентироваться в боте.

## Acceptance Criteria

1. **Given** пользователь находится в боте
   **When** отображается главное меню
   **Then** доступны кнопки навигации по Rule of 3 (≤3 кнопки на уровень)
   **And** переходы работают без задержек
   **And** кнопка «Назад» доступна на каждом уровне
   **And** согласие на обработку ПД запрашивается при первом значимом действии (FR43)

2. **Given** пользователь находится на любом экране
   **When** нажимает кнопку "Назад"
   **Then** возвращается на предыдущий уровень навигации
   **And** состояние интерфейса корректно восстанавливается

3. **Given** пользователь выполняет первое значимое действие (например, нажимает "Забронировать" или "Добавить в избранное")
   **When** система определяет, что согласие на ПД еще не получено
   **Then** отображается запрос на согласие с обработкой персональных данных
   **And** после получения согласия действие продолжается автоматически
   **And** повторный запрос согласия не требуется при следующих действиях

4. **And** главное меню содержит максимум 3 кнопки (Rule of 3):
   - "🔍 Поиск квартир"
   - "📋 Мои бронирования"
   - "❓ Помощь"

5. **And** весь пользовательский текст строго на русском языке (FR9)

6. **And** fail-soft behaviour сохраняется на всех шагах:
   - При исключении в handler — логировать ошибку и отправлять пользователю дружелюбное сообщение
   - Всегда вызывать `callback.answer()` или `message.answer()` для корректного UX

## Tasks / Subtasks

- [x] **Task 1: Создать главное меню с базовой навигацией** (AC: #1, #4)
  - [x] Создать новый handler `on_main_menu` в `backend/bot/handlers/common.py`
  - [x] Создать helper функцию `_build_main_menu_keyboard()` с 3 кнопками
  - [x] Отправить сообщение с меню при команде `/menu` или callback `main_menu`

- [ ] **Task 2: Реализовать navigation stack для кнопки "Назад"** (AC: #2)
  - [ ] Расширить session structure для хранения navigation history в Redis
  - [ ] Добавить helper `_push_nav_state(user_id, state)` для добавления в стек
  - [ ] Добавить helper `_pop_nav_state(user_id)` для возврата на предыдущий уровень
  - [ ] Создать handler `on_back_button` для обработки callback `nav_back`

- [ ] **Task 3: Добавить кнопку "Назад" на все существующие экраны** (AC: #2)
  - [ ] Обновить keyboards в `backend/bot/handlers/search.py` с кнопкой "Назад"
  - [ ] Обновить keyboards в `backend/bot/handlers/welcome.py` с кнопкой "Назад"
  - [ ] Убедиться, что Rule of 3 соблюдается (если 3 кнопки уже есть, заменить одну на "Назад")

- [ ] **Task 4: Реализовать запрос согласия на обработку ПД** (AC: #3)
  - [ ] Добавить поле `pd_consent_given: bool` в модель User (или в Redis session)
  - [ ] Создать middleware или helper `_check_pd_consent(user_id)` для проверки согласия
  - [ ] Создать handler `on_pd_consent_request` для отображения текста согласия + inline keyboard "Согласен" / "Отказаться"
  - [ ] При первом значимом действии (например, `search_book`, `search_favorite`) проверить `pd_consent_given`
  - [ ] Если согласия нет — показать запрос, после получения — продолжить действие

- [ ] **Task 5: Создать handler для раздела "Мои бронирования"** (AC: #4)
  - [ ] Создать заглушку в `backend/bot/handlers/common.py`: `on_my_bookings`
  - [ ] Отправить сообщение: "Раздел 'Мои бронирования' появится в Epic 4. Пока можешь вернуться к поиску."
  - [ ] Добавить inline keyboard с кнопкой "🔍 Вернуться к поиску" и "◀️ Назад"

- [ ] **Task 6: Создать handler для раздела "Помощь"** (AC: #4)
  - [ ] Создать заглушку в `backend/bot/handlers/common.py`: `on_help`
  - [ ] Отправить сообщение с кратким описанием возможностей бота
  - [ ] Добавить inline keyboard с кнопкой "◀️ Назад в меню"

- [ ] **Task 7: Обновить welcome flow для интеграции с главным меню** (AC: #1)
  - [ ] После приветствия и демо-поиска показывать главное меню
  - [ ] Обновить `backend/bot/handlers/welcome.py` для перехода к главному меню

- [ ] **Task 8: Добавить тесты для навигации и согласия на ПД** (AC: #1-6)
  - [ ] Happy path: главное меню → раздел → "Назад" → главное меню
  - [ ] Navigation stack: несколько переходов → "Назад" → корректный возврат
  - [ ] PD consent: первое значимое действие → запрос согласия → действие продолжается
  - [ ] PD consent: повторное действие → согласие не запрашивается снова
  - [ ] Fail-soft: исключение в handler → дружелюбное сообщение

## Dev Notes

### Developer Context

**Текущее состояние (из Story 1.1-1.3):**
- В `backend/bot/handlers/start.py` реализован `/start` command
- В `backend/bot/handlers/welcome.py` реализован welcome-сценарий
- В `backend/bot/handlers/search.py` реализован базовый поиск и preview/detail карточки
- Session-механизм (`_SESSIONS`) используется для хранения результатов поиска

**Цель Story 1.4:**
- Добавить постоянное главное меню для навигации
- Реализовать navigation stack для кнопки "Назад"
- Добавить запрос согласия на обработку ПД при первом значимом действии
- Подготовить структуру для будущих разделов (Мои бронирования, Помощь)

**UX-принципы:**
- Rule of 3: максимум 3 кнопки на уровень (из UX spec)
- Zero-friction: минимум шагов для основных действий
- Fail-soft: дружелюбные сообщения при ошибках
- Always answer callbacks: обязательно вызывать `callback.answer()`

### Technical Requirements

- **Платформа:** Telegram Bot (aiogram 3.24.0), НЕ Mini App
- **Navigation Stack:** Хранить в Redis с TTL 30 мин (как и существующие sessions)
- **PD Consent:** Хранить в PostgreSQL в таблице `users` (поле `pd_consent_given: bool`)
- **Inline Keyboard:** Использовать `InlineKeyboardBuilder` из aiogram.utils.keyboard
- **Session Management:** Переиспользовать существующую логику `_SESSIONS[user_id]` или создать отдельный механизм для navigation
- **Error Handling:** Всегда логировать исключения, отправлять fail-soft сообщения пользователю

### Architecture Compliance

- **Слой обработчиков:** Основные изменения в `backend/bot/handlers/common.py`, минорные обновления в `search.py` и `welcome.py`
- **Модель User:** Обновить `backend/shared/models.py` для добавления поля `pd_consent_given`
- **Migration:** Создать Alembic migration для добавления поля в таблицу `users`
- **Webhook-архитектура:** Не менять transport/infra часть, только handlers
- **Rule of 3:** Максимум 3 кнопки на уровень (из UX spec), применяется ко всем keyboards
- **Conversational UX:** Короткие блоки текста на русском, без технического жаргона
- **Переиспользование кода:** Максимально использовать существующие helper-функции

### Library / Framework Requirements

- **aiogram 3.24.0:** Основной фреймворк
- **Redis:** Для navigation stack (если не использовать PostgreSQL)
- **SQLModel:** Для модели User
- **Alembic:** Для миграции БД
- **Typing:** Использовать аннотации типов
- **Logging:** `logger = logging.getLogger(__name__)` для всех исключений
- **No new dependencies:** Не добавлять новые Python-пакеты для Story 1.4

### File Structure Requirements

- **Основной файл:** `backend/bot/handlers/common.py`
  - Создать handlers: `on_main_menu`, `on_my_bookings`, `on_help`, `on_back_button`, `on_pd_consent_request`
  - Создать helpers: `_build_main_menu_keyboard()`, `_push_nav_state()`, `_pop_nav_state()`, `_check_pd_consent()`

- **Обновления:**
  - `backend/bot/handlers/search.py`: добавить кнопку "Назад" на keyboards
  - `backend/bot/handlers/welcome.py`: интеграция с главным меню
  - `backend/shared/models.py`: добавить поле `pd_consent_given: bool` в модель User
  - `backend/app/alembic/versions/`: создать новую миграцию

- **Тесты:** `backend/bot/tests/test_common_handler.py`
  - Создать новый файл для тестов навигации и PD consent
  - Добавить тесты на navigation stack, главное меню, PD consent flow

- **Не трогать:** `backend/bot/main.py`, `backend/app/*`, `backend/workers/*`

### Testing Requirements

- **Обязательные тесты:**
  1. **Main menu:** callback `main_menu` → меню с 3 кнопками отображается
  2. **Navigation stack:** главное меню → раздел → "Назад" → главное меню
  3. **PD consent:** первое значимое действие → запрос согласия → действие продолжается
  4. **PD consent (repeat):** повторное действие → согласие не запрашивается
  5. **Fail-soft:** Mock исключения в handler → дружелюбное сообщение отправлено

- **Регрессионные тесты:** Убедиться, что существующие тесты из Story 1.1-1.3 продолжают проходить

- **Ручная матрица проверок:**
  - [ ] Нажать "/menu" → главное меню отображается
  - [ ] Нажать "Поиск" → поиск квартир запускается
  - [ ] Нажать "Мои бронирования" → заглушка отображается
  - [ ] Нажать "Помощь" → help message отображается
  - [ ] Нажать "Назад" → возврат на предыдущий уровень
  - [ ] Первое значимое действие → запрос согласия на ПД → действие продолжается

### Previous Story Intelligence

**Из Story 1.1 (Welcome):**
- Важность always answering callback queries
- Fail-soft на каждом этапе
- Короткие RU-тексты без технического жаргона

**Из Story 1.2 (Demo Search):**
- Session-механизм работает хорошо: `_SESSIONS[user_id]` для хранения состояния
- Helper-функции (`_send_callback_text`, `_user_id_from_callback`, `_bot_from_callback`) успешно переиспользуются
- Inline keyboard с `InlineKeyboardBuilder` — стандартный паттерн
- Defensive programming: всегда проверять наличие `session`, `callback.message`, `from_user`

**Из Story 1.3 (Apartment Card Preview):**
- Галерея фото через `send_media_group()` для UX-friendly отображения
- Detail keyboard с 3 кнопками (Rule of 3)
- Возврат к поиску через callback `search_back` работает корректно
- Всегда оборачивать в try-except с logging и fail-soft

**Ключевые уроки для Story 1.4:**
- Переиспользовать session-механизм для navigation stack
- Добавить helper-функции для navigation state management
- Всегда проверять `callback.message` и `from_user` перед использованием
- Логировать все исключения с контекстом
- Короткие сообщения на русском языке

### Git Intelligence Summary

**Последние коммиты:**
- `06ec6d5`: Story 1-0 initialization + code review fixes — установил baseline bot-структуры
- Текущие паттерны: отдельные handler-модули, подключение через router, unit tests обязательны

**Файловая структура bot-слоя устоялась:**
- `backend/bot/handlers/` — один файл на feature
- `backend/bot/main.py` — регистрация routers
- `backend/bot/tests/` — unit tests для handlers

**Story 1.4 может безопасно:**
- Создать новый `common.py` для общей навигации
- Обновить существующие handlers для интеграции с navigation stack
- Добавить миграцию БД для поля `pd_consent_given`

### Latest Tech Information

**Telegram Bot API (версия 9.3, 31 декабря 2025):**
- Inline keyboard: до 8 кнопок в одном сообщении (мы используем 3 по UX-принципу)
- `callback.answer()` обязателен для всех callback queries (иначе пользователь видит "загрузку" бесконечно)

**aiogram 3.24.0:**
- Stable на PyPI, поддерживает Bot API 9.3
- `InlineKeyboardBuilder` — удобный helper для построения клавиатур
- Middleware для обработки согласия на ПД можно реализовать через `BaseMiddleware`

**Redis 8:**
- TTL для session context: 30 мин (стандарт из архитектуры)
- Navigation stack: можно хранить как список в Redis с ключом `nav:{user_id}`

**PostgreSQL 18:**
- Добавление поля `pd_consent_given BOOLEAN DEFAULT FALSE` — простая миграция
- Использовать `AsyncSession` для всех DB операций (из архитектуры)

**Best practices для Story 1.4:**
- Использовать middleware для проверки PD consent вместо дублирования кода в каждом handler
- Navigation stack: хранить как JSON в Redis с TTL 30 мин
- Главное меню: reply keyboard или inline keyboard? — inline keyboard (более UX-friendly для navigation)

### Project Structure Notes

**Изменения концентрируются в bot-слое:**
- `backend/bot/handlers/common.py` — новый файл с navigation handlers
- `backend/bot/handlers/search.py` — минорные обновления (добавление кнопки "Назад")
- `backend/bot/handlers/welcome.py` — интеграция с главным меню
- `backend/shared/models.py` — добавление поля `pd_consent_given`
- `backend/bot/tests/test_common_handler.py` — новые тесты

**Naming conventions:**
- Callback data: `nav_*` для навигации (e.g., `nav_back`, `main_menu`)
- Handler functions: `on_<callback_name>` (e.g., `on_main_menu`, `on_back_button`)
- Helper functions: `_<verb>_<noun>` (e.g., `_build_main_menu_keyboard`, `_check_pd_consent`)
- Private constants: `_UPPERCASE_WITH_UNDERSCORES`

**Соответствие UX spec:**
- Rule of 3: максимум 3 кнопки в главном меню и на каждом уровне
- Conversational-first: короткие блоки текста, без форм
- Zero-friction: минимум шагов для основных действий

### Project Context Reference

**Relevant planning artifacts:**
- [Epic 1 Story 1.4 from epics.md](_bmad-output/planning-artifacts/epics.md#Story-1.4)
- [FR8 from prd.md](_bmad-output/planning-artifacts/prd.md#FR8)
- [FR43 from prd.md](_bmad-output/planning-artifacts/prd.md#FR43)
- [UX Rule of 3 from ux-design-specification.md](_bmad-output/planning-artifacts/ux-design-specification.md)
- [Architecture: Bot Framework](architecture.md#Bot-Framework)
- [Previous Story 1.1](1-1-telegram-bot-welcome.md)
- [Previous Story 1.2](1-2-demo-search-without-registration.md)
- [Previous Story 1.3](1-3-apartment-card-preview.md)

### Story Completion Status

- Story status: `ready-for-dev`
- Completion note: Ultimate context engine analysis completed - comprehensive developer guide created

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Story 1.4`]
- [Source: `_bmad-output/planning-artifacts/epics.md#Epic 1`]
- [Source: `_bmad-output/planning-artifacts/prd.md#FR8`]
- [Source: `_bmad-output/planning-artifacts/prd.md#FR43`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Bot Framework`]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md#Rule of 3`]
- [Source: `_bmad-output/implementation-artifacts/1-1-telegram-bot-welcome.md`]
- [Source: `_bmad-output/implementation-artifacts/1-2-demo-search-without-registration.md`]
- [Source: `_bmad-output/implementation-artifacts/1-3-apartment-card-preview.md`]
- [Source: `backend/bot/handlers/`]
- [Source: `https://core.telegram.org/bots/api-changelog`]

## Dev Agent Record

### Agent Model Used

(To be filled by dev agent)

### Implementation Plan

(To be filled by dev agent)

### Debug Log References

(To be filled by dev agent)

### Completion Notes List

(To be filled by dev agent)

### File List

(To be filled by dev agent)
