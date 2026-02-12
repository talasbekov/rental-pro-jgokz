# Story 1.4: Navigation Stack и Согласие на Обработку ПД

Status: ready-for-dev

**Story Key:** `1-4-basic-navigation-structured-flow`
**Epic:** 1 — Первое касание и знакомство с продуктом
**Дата переработки:** 2026-02-12

**Коротко:** Реализовать navigation stack для иерархической навигации с inline-кнопками "◀️ Назад", которые возвращают пользователя на предыдущий уровень. Добавить flow запроса согласия на обработку ПД (FR43) при первом значимом действии. Интегрироваться с уже существующим ReplyKeyboard меню из Story 1.1.5.

⚠️ **ВАЖНЫЙ КОНТЕКСТ:** Story 1.1.5 (ReplyKeyboard persistent menu) была добавлена в спринт ПОСЛЕ создания первоначальной версии Story 1.4 и уже реализовала постоянное меню с кнопками. Эта история теперь фокусируется ТОЛЬКО на недостающей функциональности: navigation stack + PD consent.

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a гость,
I want использовать inline-кнопки "◀️ Назад" для возврата на предыдущий уровень навигации,
so that легко перемещаться по иерархии экранов бота без потери контекста.

## Acceptance Criteria

### AC#1: Navigation Stack для иерархической навигации

**Given** пользователь находится на любом промежуточном экране бота (например, детальная карточка квартиры, help screen)
**When** нажимает inline-кнопку "◀️ Назад"
**Then** возвращается на предыдущий уровень навигации (например, из детальной карточки → к списку результатов поиска)
**And** состояние предыдущего экрана корректно восстанавливается (например, текущий индекс в результатах поиска)
**And** navigation stack хранится в Redis с TTL 30 мин (как и существующие sessions)

### AC#2: Inline-кнопки "Назад" на всех промежуточных экранах

**Given** пользователь просматривает экраны бота
**When** находится на любом промежуточном экране (не главное меню)
**Then** доступна inline-кнопка "◀️ Назад" для возврата
**And** кнопка НЕ появляется на главном меню или welcome screen (нет предыдущего уровня)
**And** Rule of 3 соблюдается: если inline-клавиатура уже имеет 3 кнопки, "Назад" добавляется в новый ряд

### AC#3: Запрос согласия на обработку ПД при первом значимом действии

**Given** пользователь выполняет первое значимое действие (например, нажимает "Забронировать" или "❤️ В избранное")
**When** система определяет, что `pd_consent_given` для этого пользователя еще не установлен
**Then** отображается запрос на согласие с текстом:
```
📋 Согласие на обработку персональных данных

Для бронирования и других действий нам нужно хранить твои данные (Telegram ID, история бронирований).

Мы обязуемся:
✓ Не передавать данные третьим лицам
✓ Хранить данные на серверах в Казахстане
✓ Удалить данные по твоему запросу

Согласен на обработку персональных данных?
```
**And** отображается inline-клавиатура с кнопками:
  - "✅ Согласен" (callback_data `pd_consent_accept`)
  - "❌ Отказаться" (callback_data `pd_consent_reject`)

### AC#4: Обработка согласия пользователя

**Given** пользователь видит запрос на согласие
**When** нажимает "✅ Согласен"
**Then** поле `pd_consent_given` в модели User устанавливается в `True`
**And** `pd_consent_timestamp` записывается (для аудита)
**And** первоначальное действие продолжается автоматически (например, переход к бронированию)
**And** повторный запрос согласия НЕ отображается при следующих значимых действиях

**Given** пользователь видит запрос на согласие
**When** нажимает "❌ Отказаться"
**Then** отображается сообщение: "Без согласия на обработку ПД мы не можем продолжить это действие. Ты можешь вернуться к поиску."
**And** `pd_consent_given` остается `False` или `None`
**And** действие НЕ выполняется
**And** пользователь может продолжить использовать бот в режиме просмотра (поиск, просмотр карточек)

### AC#5: Интеграция с ReplyKeyboard из Story 1.1.5

**Given** Story 1.1.5 уже реализовала постоянное ReplyKeyboard меню
**Then** Story 1.4 НЕ дублирует эту функциональность
**And** новый navigation stack работает параллельно с ReplyKeyboard:
  - ReplyKeyboard = **постоянная навигация** по основным разделам (Поиск, Бронирования, Избранное, Помощь)
  - Navigation Stack = **иерархическая навигация** внутри разделов (inline-кнопки "Назад")

### AC#6: Fail-soft поведение

**And** при исключении в navigation handler — логировать ошибку и отправлять пользователю дружелюбное сообщение
**And** всегда вызывать `callback.answer()` для корректного UX
**And** если navigation stack поврежден или истек — перенаправить на главное меню с сообщением "Сессия истекла. Начни с главного меню."

### AC#7: Весь пользовательский текст на русском языке (FR9)

**And** весь пользовательский текст строго на русском языке
**And** технические термины НЕ используются в сообщениях пользователю

## Tasks / Subtasks

### ✅ ПРОПУЩЕНО: Задачи из оригинальной Story 1.4, которые уже реализованы в Story 1.1.5
- ~~Task 1: Создать главное меню~~ → Реализовано в 1.1.5 (ReplyKeyboard)
- ~~Task 5: "Мои бронирования" handler~~ → Реализовано в 1.1.5
- ~~Task 6: "Помощь" handler~~ → Реализовано в 1.1.5
- ~~Task 7: Welcome flow integration~~ → Реализовано в 1.1.5

### 📋 НОВЫЕ ЗАДАЧИ для переработанной Story 1.4

- [ ] **Task 1: Создать navigation stack механизм в Redis** (AC: #1)
  - [ ] Создать helper `_push_nav_state(user_id: int, state: str, context: dict)` для добавления уровня в стек
  - [ ] Создать helper `_pop_nav_state(user_id: int) -> tuple[str, dict] | None` для возврата на предыдущий уровень
  - [ ] Создать helper `_get_current_nav_state(user_id: int) -> tuple[str, dict] | None` для получения текущего состояния
  - [ ] Хранить в Redis с ключом `nav_stack:{user_id}` как JSON list, TTL 30 мин
  - [ ] Каждый элемент стека: `{"state": "search_results", "context": {"query": "...", "index": 2}}`

- [ ] **Task 2: Добавить inline-кнопку "Назад" на существующие экраны** (AC: #2)
  - [ ] Обновить `_build_detail_card_keyboard()` в `search.py`: добавить "◀️ Назад" в новый ряд (уже есть 3 кнопки: Забронировать, ❤️, Назад к поиску → теперь 4 кнопки, layout 3+1)
  - [ ] **ВНИМАНИЕ:** Кнопка "Назад к поиску" (callback `search_back`) в detail keyboard УЖЕ работает как navigation — переиспользовать ее вместо создания новой
  - [ ] Обновить help screen: добавить inline-кнопку "◀️ Назад в меню" (callback `nav_back_to_menu`)
  - [ ] Создать unified handler `on_nav_back` для обработки `nav_back` callback

- [ ] **Task 3: Обновить модель User для хранения PD consent** (AC: #3, #4)
  - [ ] Добавить поле `pd_consent_given: bool | None = Field(default=None)` в модель `User` (`backend/shared/models.py`)
  - [ ] Добавить поле `pd_consent_timestamp: datetime | None = Field(default=None)` для аудита
  - [ ] Создать Alembic migration для добавления полей в таблицу `users`
  - [ ] Обновить `UserBase` schema для включения новых полей (опционально для API)

- [ ] **Task 4: Реализовать flow запроса PD consent** (AC: #3, #4)
  - [ ] Создать helper `_check_pd_consent(user_id: int) -> bool` для проверки согласия через DB
  - [ ] Создать middleware или decorator `@require_pd_consent` для применения к "значимым действиям"
  - [ ] Создать handler `on_pd_consent_request` для отображения текста согласия + inline keyboard
  - [ ] Создать handler `on_pd_consent_accept` для сохранения согласия в DB и продолжения действия
  - [ ] Создать handler `on_pd_consent_reject` для отображения сообщения об отказе

- [ ] **Task 5: Применить PD consent gate к значимым действиям** (AC: #4)
  - [ ] Обернуть `on_search_book` (бронирование) в `@require_pd_consent` decorator
  - [ ] Обернуть `on_search_favorite` (избранное) в `@require_pd_consent` decorator
  - [ ] При согласии пользователя — продолжить первоначальное действие (через callback data context)

- [ ] **Task 6: Fail-soft обработка для navigation и consent** (AC: #6)
  - [ ] Обернуть все navigation handlers в try-except с logging
  - [ ] При ошибке отправлять дружелюбное сообщение + ReplyKeyboard
  - [ ] Если navigation stack поврежден — redirect на главное меню с "Сессия истекла"

- [ ] **Task 7: Написать тесты для navigation stack и PD consent** (AC: #1-7)
  - [ ] Happy path: navigation stack push → pop → корректное восстановление состояния
  - [ ] Navigation "Назад": детальная карточка → "Назад" → preview-карточка с правильным индексом
  - [ ] PD consent: первое значимое действие → запрос согласия → действие продолжается
  - [ ] PD consent (reject): отказ → действие НЕ выполняется
  - [ ] PD consent (repeat): повторное действие → согласие не запрашивается снова
  - [ ] Fail-soft: navigation stack expired → redirect на главное меню
  - [ ] Integration: ReplyKeyboard + navigation stack работают параллельно

## Dev Notes

### Developer Context

**Контекст Sprint Change (2026-02-12):**

Story 1.4 была изначально создана для реализации главного меню и навигации, но позже в спринт была добавлена **Story 1.1.5 (ReplyKeyboard Persistent Menu)**, которая УЖЕ реализовала постоянное меню навигации с 4 кнопками.

**Что УЖЕ сделано в Story 1.1.5:**
- ✅ ReplyKeyboard с 4 кнопками (🔍 Поиск, 📋 Бронирования, ❤️ Избранное, ❓ Помощь)
- ✅ Handlers для всех кнопок в `backend/bot/handlers/common.py`
- ✅ Заглушки для "Мои бронирования" и "Избранное"
- ✅ Интеграция с welcome flow и search
- ✅ Fail-soft поведение

**Что ОТСУТСТВУЕТ и реализуется в ЭТОЙ истории (1.4 переработка):**
- ❌ **Navigation stack** для иерархической навигации (inline-кнопки "Назад")
- ❌ **PD consent flow** (FR43) при первом значимом действии
- ❌ Inline-кнопки "◀️ Назад" на промежуточных экранах для возврата по уровням

**Архитектурное разделение:**
- **ReplyKeyboard (Story 1.1.5)** = Постоянная навигация по основным разделам (всегда видна внизу экрана)
- **Navigation Stack (Story 1.4)** = Иерархическая навигация внутри разделов (inline-кнопки "Назад" для возврата на предыдущий уровень)

**Цель Story 1.4 (после переработки):**
- Добавить navigation stack (Redis-based) для иерархической навигации
- Реализовать inline-кнопки "◀️ Назад" на промежуточных экранах
- Добавить flow запроса согласия на обработку ПД (FR43)
- Интегрироваться с существующим ReplyKeyboard из 1.1.5

**UX-принципы:**
- Два уровня навигации работают параллельно:
  - **Horizontal navigation** (ReplyKeyboard): переключение между основными разделами
  - **Vertical navigation** (Navigation Stack): погружение/возврат внутри раздела
- PD consent запрашивается ОДИН РАЗ при первом значимом действии (не при просмотре)
- Fail-soft: навигация не должна ломать пользовательский опыт при ошибках

### Technical Requirements

- **Платформа:** Telegram Bot (aiogram 3.24.0), НЕ Mini App
- **Navigation Stack Storage:** Redis с TTL 30 мин (как существующие sessions)
  - Ключ: `nav_stack:{user_id}`
  - Формат: JSON list `[{"state": "...", "context": {...}}, ...]`
  - Push на каждый новый уровень, Pop при "Назад"
- **PD Consent Storage:** PostgreSQL в таблице `users`
  - Поле: `pd_consent_given: bool | None`
  - Поле: `pd_consent_timestamp: datetime | None` (для аудита)
- **Inline Keyboard:** Использовать `InlineKeyboardBuilder` из aiogram.utils.keyboard
- **Decorator Pattern:** `@require_pd_consent` для применения к handlers
- **Error Handling:** Всегда логировать исключения, отправлять fail-soft сообщения + ReplyKeyboard

### Architecture Compliance

- **Слой обработчиков:** Основные изменения в `backend/bot/handlers/common.py` и `backend/bot/handlers/search.py`
- **Модель User:** Обновить `backend/shared/models.py` для добавления полей PD consent
- **Migration:** Создать Alembic migration для добавления полей в таблицу `users`
- **Redis Navigation Stack:** Создать helpers в `backend/bot/utils/navigation.py` для управления стеком
- **Webhook-архитектура:** Не менять transport/infra часть, только handlers
- **Rule of 3:** Максимум 3 кнопки в ряд (из UX spec), применяется ко всем keyboards; при добавлении "Назад" к keyboard с 3 кнопками — создать новый ряд
- **Conversational UX:** Короткие блоки текста на русском, без технического жаргона
- **Переиспользование кода:** Максимально использовать существующие helper-функции из 1.1.5

### Library / Framework Requirements

- **aiogram 3.24.0:** Основной фреймворк
- **Redis:** Для navigation stack (через существующий connection pool)
- **SQLModel + AsyncSession:** Для модели User и PD consent
- **Alembic:** Для миграции БД
- **Typing:** Использовать аннотации типов
- **Logging:** `logger = logging.getLogger(__name__)` для всех исключений
- **No new dependencies:** Не добавлять новые Python-пакеты для Story 1.4

### File Structure Requirements

- **Создать:** `backend/bot/utils/navigation.py`
  - Helpers: `_push_nav_state()`, `_pop_nav_state()`, `_get_current_nav_state()`
  - Redis key management для navigation stack

- **Обновить:** `backend/shared/models.py`
  - Добавить поля `pd_consent_given: bool | None` и `pd_consent_timestamp: datetime | None` в модель User

- **Создать:** `backend/app/alembic/versions/YYYYMMDD_HHMM_add_pd_consent_to_users.py`
  - Alembic migration для добавления полей в таблицу users

- **Обновить:** `backend/bot/handlers/common.py`
  - Создать handlers: `on_nav_back`, `on_nav_back_to_menu`, `on_pd_consent_request`, `on_pd_consent_accept`, `on_pd_consent_reject`
  - Создать decorator/middleware: `@require_pd_consent`
  - Создать helper: `_check_pd_consent(user_id: int) -> bool`

- **Обновить:** `backend/bot/handlers/search.py`
  - Обновить detail keyboard: добавить "◀️ Назад" (если еще нет `search_back`)
  - Применить `@require_pd_consent` к `on_search_book` и `on_search_favorite`

- **Создать:** `backend/bot/tests/test_navigation_stack.py`
  - Тесты для navigation stack (push, pop, restore)

- **Создать:** `backend/bot/tests/test_pd_consent.py`
  - Тесты для PD consent flow (request, accept, reject, repeat)

- **Не трогать:** `backend/bot/main.py`, `backend/bot/keyboards/reply.py` (уже есть в 1.1.5), `backend/app/*` (кроме alembic), `backend/workers/*`

### Testing Requirements

- **Обязательные тесты:**
  1. **Navigation stack push/pop:** главное меню → раздел → "Назад" → главное меню, state восстановлен
  2. **Navigation "Назад" из detail:** детальная карточка → "Назад" → preview-карточка с правильным индексом
  3. **PD consent (first time):** первое значимое действие → запрос согласия → "Согласен" → действие продолжается
  4. **PD consent (reject):** запрос согласия → "Отказаться" → действие НЕ выполняется
  5. **PD consent (repeat):** повторное действие → согласие не запрашивается (уже дано)
  6. **Navigation stack expired:** expired session → redirect на главное меню с сообщением
  7. **Fail-soft navigation:** исключение в nav handler → дружелюбное сообщение + ReplyKeyboard
  8. **Integration:** ReplyKeyboard + navigation stack работают параллельно без конфликтов

- **Регрессионные тесты:** Убедиться, что существующие тесты из Story 1.1-1.3 и 1.1.5 продолжают проходить

- **Ручная матрица проверок:**
  - [ ] Нажать "Поиск" (ReplyKeyboard) → поиск запускается
  - [ ] Из результатов нажать "Подробнее" → детальная карточка
  - [ ] Нажать "◀️ Назад" (inline) → вернуться к списку результатов
  - [ ] Первое нажатие "Забронировать" → запрос согласия на ПД
  - [ ] Согласиться → бронирование продолжается (заглушка Epic 4)
  - [ ] Повторное "Забронировать" → согласие не запрашивается
  - [ ] Нажать "Помощь" (ReplyKeyboard) → help screen
  - [ ] Из help нажать "◀️ Назад" (inline) → главное меню
  - [ ] Проверить на мобильном Telegram: оба типа навигации работают корректно

### Previous Story Intelligence

**Из Story 1.1.5 (ReplyKeyboard — DONE):**
- ReplyKeyboard создается через `_build_main_reply_keyboard()` в `backend/bot/keyboards/reply.py`
- Все handlers в `common.py` сохраняют ReplyKeyboard через `reply_markup=_build_main_reply_keyboard()`
- Message handlers используют `F.text ==` filter для кнопок ReplyKeyboard
- Fail-soft: все handlers оборачивают в try-except и возвращают `_FAIL_SOFT_TEXT` + ReplyKeyboard
- Router order важен: ReplyKeyboard handlers должны быть ДО поискового handler'а (чтобы не перехватывать текст кнопок)

**Из Story 1.1 (Welcome):**
- Важность always answering callback queries
- Fail-soft на каждом этапе
- Короткие RU-тексты без технического жаргона
- Silent auth через Telegram ID (уже работает)

**Из Story 1.2 (Demo Search):**
- Session-механизм `_SESSIONS[user_id]` для хранения результатов поиска и индекса
- Helper-функции (`_send_callback_text`) успешно переиспользуются
- Defensive programming: всегда проверять наличие `session`, `callback.message`, `from_user`

**Из Story 1.3 (Apartment Card Preview):**
- Inline-кнопка "Назад к поиску" (callback `search_back`) УЖЕ работает как navigation
- Detail keyboard использует `_build_detail_card_keyboard()` с 3 кнопками (Rule of 3)
- Всегда оборачивать в try-except с logging и fail-soft

**Ключевые уроки для Story 1.4:**
- Переиспользовать session-механизм для navigation stack (Redis, TTL 30 мин)
- Navigation stack должен быть отдельным механизмом (НЕ смешивать с `_SESSIONS`)
- PD consent проверяется через middleware/decorator для удобства применения
- Inline-кнопки "Назад" создаются динамически на каждом экране (не в ReplyKeyboard)
- Логировать все исключения с контекстом, использовать `_FAIL_SOFT_TEXT`

### Git Intelligence Summary

**Последние коммиты:**
- `5502a16`: Tg bot for rental MVP LLM — текущий baseline
- `06ec6d5`: Story 1-0 initialization + code review fixes
- Stories 1.1, 1.1.5, 1.2, 1.3 завершены — навигация через ReplyKeyboard работает

**Файловая структура bot-слоя устоялась:**
- `backend/bot/handlers/` — один файл на feature
- `backend/bot/keyboards/reply.py` — ReplyKeyboard builders (из 1.1.5)
- `backend/bot/main.py` — регистрация routers
- `backend/bot/tests/` — unit tests для handlers

**Story 1.4 может безопасно:**
- Создать новый `utils/navigation.py` для navigation stack helpers
- Обновить `common.py` с новыми handlers для PD consent
- Обновить `shared/models.py` с полями PD consent
- Добавить Alembic migration для БД
- Обновить `search.py` для интеграции с PD consent decorator

### Latest Tech Information

**Telegram Bot API (версия 9.3, 31 декабря 2025):**
- Inline keyboard: до 8 кнопок в одном сообщении (мы используем 3 по UX-принципу)
- `callback.answer()` обязателен для всех callback queries

**aiogram 3.24.0 (latest, 10 февраля 2026):**
- Stable на PyPI, поддерживает Bot API 9.3
- `InlineKeyboardBuilder` — удобный helper для построения клавиатур
- Middleware для обработки согласия на ПД можно реализовать через `BaseMiddleware` или decorator pattern

**Redis 8:**
- TTL для session context: 30 мин (стандарт из архитектуры)
- Navigation stack: можно хранить как JSON list в Redis с ключом `nav_stack:{user_id}`
- Пример: `await redis.setex(f"nav_stack:{user_id}", 1800, json.dumps([...]))`

**PostgreSQL 18 + SQLModel:**
- Добавление полей `pd_consent_given: bool | None` и `pd_consent_timestamp: datetime | None` — простая миграция
- Использовать `AsyncSession` для всех DB операций (из архитектуры)
- Alembic migration template: `alembic revision -m "add_pd_consent_to_users"`

**GDPR PD Consent Best Practices (2026):**
- Clear and affirmative opt-ins (unchecked box before starting) — применить к первому значимому действию
- Timestamped log of consent (who, when, what, how) — сохранять `pd_consent_timestamp`
- Easy withdrawal (будет в Epic 6 — право на удаление данных)
- Transparent privacy policy — текст согласия должен быть понятным

**Источники:**
- [aiogram 3 documentation](https://docs.aiogram.dev/)
- [GDPR Chatbot Compliance Guide](https://quickchat.ai/post/gdpr-compliant-chatbot-guide)
- [Complete GDPR Compliance 2026](https://secureprivacy.ai/blog/gdpr-compliance-2026)

**Best practices для Story 1.4:**
- Использовать decorator `@require_pd_consent` для применения к handlers вместо дублирования кода
- Navigation stack: хранить как JSON list в Redis с TTL 30 мин
- PD consent text: короткий, понятный, с эмодзи для читабельности
- Inline "Назад" кнопки: добавлять динамически на каждом экране, где есть предыдущий уровень

### Project Structure Notes

**Изменения концентрируются в bot-слое:**
- `backend/bot/utils/navigation.py` — новый файл с navigation stack helpers
- `backend/bot/handlers/common.py` — новые handlers для PD consent и navigation
- `backend/bot/handlers/search.py` — применение `@require_pd_consent` к значимым действиям
- `backend/shared/models.py` — добавление полей PD consent
- `backend/app/alembic/versions/` — новая миграция
- `backend/bot/tests/test_navigation_stack.py` — новые тесты
- `backend/bot/tests/test_pd_consent.py` — новые тесты

**Naming conventions:**
- Navigation callback data: `nav_*` (e.g., `nav_back`, `nav_back_to_menu`)
- PD consent callback data: `pd_consent_*` (e.g., `pd_consent_accept`, `pd_consent_reject`)
- Handler functions: `on_<callback_name>` (e.g., `on_nav_back`, `on_pd_consent_accept`)
- Helper functions: `_<verb>_<noun>` (e.g., `_push_nav_state`, `_check_pd_consent`)
- Private constants: `_UPPERCASE_WITH_UNDERSCORES` (e.g., `_PD_CONSENT_TEXT`)

**Соответствие UX spec:**
- Rule of 3: максимум 3 кнопки в ряд, при добавлении "Назад" — новый ряд
- Conversational-first: короткие блоки текста, без форм
- Zero-friction: PD consent запрашивается ТОЛЬКО при первом значимом действии (не при просмотре)

### Project Context Reference

**Relevant planning artifacts:**
- [Epic 1 Story 1.4 from epics.md](_bmad-output/planning-artifacts/epics.md#Story-1.4)
- [FR8 from prd.md](_bmad-output/planning-artifacts/prd.md#FR8) — Structured flow (базовый)
- [FR43 from prd.md](_bmad-output/planning-artifacts/prd.md#FR43) — Согласие на обработку ПД при первом значимом действии
- [UX Rule of 3 from ux-design-specification.md](_bmad-output/planning-artifacts/ux-design-specification.md)
- [Architecture: Bot Framework](architecture.md#Bot-Framework)
- [Architecture: Redis Session Context](architecture.md#Redis)
- [Previous Story 1.1](1-1-telegram-bot-welcome.md)
- [Previous Story 1.1.5](1-1.5-reply-keyboard-persistent-menu.md) — **КРИТИЧЕСКИЙ КОНТЕКСТ**
- [Previous Story 1.2](1-2-demo-search-without-registration.md)
- [Previous Story 1.3](1-3-apartment-card-preview.md)

### Story Completion Status

- Story status: `ready-for-dev`
- Completion note: Story completely rewritten post-1.1.5 to focus on navigation stack + PD consent, removing duplication with ReplyKeyboard persistent menu. Ultimate context engine analysis completed with 2026 GDPR best practices and aiogram 3.24.0 navigation patterns.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Story 1.4`]
- [Source: `_bmad-output/planning-artifacts/epics.md#Epic 1`]
- [Source: `_bmad-output/planning-artifacts/prd.md#FR8`]
- [Source: `_bmad-output/planning-artifacts/prd.md#FR43`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Bot Framework`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Redis`]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md#Rule of 3`]
- [Source: `_bmad-output/implementation-artifacts/1-1-telegram-bot-welcome.md`]
- [Source: `_bmad-output/implementation-artifacts/1-1.5-reply-keyboard-persistent-menu.md`]
- [Source: `_bmad-output/implementation-artifacts/1-2-demo-search-without-registration.md`]
- [Source: `_bmad-output/implementation-artifacts/1-3-apartment-card-preview.md`]
- [Source: `backend/bot/handlers/`]
- [Source: `backend/bot/keyboards/reply.py`]
- [Source: `https://docs.aiogram.dev/`]
- [Source: `https://quickchat.ai/post/gdpr-compliant-chatbot-guide`]
- [Source: `https://secureprivacy.ai/blog/gdpr-compliance-2026`]

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
