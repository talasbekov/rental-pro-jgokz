# Story 1.2: Демо-поиск квартир без регистрации

Status: done

**Story Key:** `1-2-demo-search-without-registration`  
**Epic:** 1 — Первое касание и знакомство с продуктом  
**Дата контекстирования:** 2026-02-10

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a гость,
I want сразу попробовать поиск квартир (по району или датам),
so that увидеть реальные предложения и понять ценность сервиса до любых обязательств.

## Acceptance Criteria

1. **Given** пользователь нажал «Попробовать поиск» в welcome-сценарии **или** отправил текстовый запрос в чат, **When** бот принимает запрос, **Then** поиск запускается без регистрации, без ввода телефона/email и без запроса документов.
2. **Given** обработка запроса завершена успешно, **When** бот формирует демо-результаты, **Then** пользователю показываются карточки квартир в формате последовательного просмотра (best match first) с обязательными полями: фото, цена, район, рейтинг.
3. **And** после первой карточки доступны понятные действия для продолжения сценария: «Следующая», «Подробнее», «Забронировать» и «❤️» (сохранение как подготовка к Epic 3, без полноценного feature-complete раздела избранного в рамках этой story).
4. **And** пользователь может последовательно листать результаты без выхода из текущего диалога; если элементов больше одного, повторный вызов «Следующая» показывает следующую карточку до исчерпания списка.
5. **And** при отсутствии совпадений бот не завершает сценарий молча: отправляет fallback-ответ с предложением упростить запрос (structured flow fallback по FR8).
6. **And** весь пользовательский текст в боте на русском языке (FR9), сообщения короткие, без технического жаргона.
7. **And** для каждого шага сценария соблюдается fail-soft поведение: при исключениях пользователь получает понятный ответ «попробуйте ещё раз /start», без silent failure.
8. **Non-goals:** в этой story не реализуются полноценный NLP-парсер Epic 3, карта Mini App, полный экран карточки с галереей и боевой ranking-движок.

## Tasks / Subtasks

- [x] Task 1: Подготовить demo search flow в Telegram-боте (AC: 1, 2, 5, 6)
- [x] Task 2: Создать/обновить обработчик поиска в `backend/bot/handlers/search.py` (AC: 1, 2, 4, 5, 7)
- [x] Task 3: Добавить представление карточки результата (минимум: фото, цена, район, рейтинг) и кнопки действий (AC: 2, 3, 4, 6)
- [x] Task 4: Связать входные точки сценария с существующим welcome-flow (`try_search` и текстовый запрос) (AC: 1, 4, 7)
- [x] Task 5: Подключить router поиска в `backend/bot/main.py` и проверить порядок middleware/router (AC: 1, 7)
- [x] Task 6: Реализовать fallback-ветку для пустых/непонятных запросов (structured flow fallback) (AC: 5, 6)
- [x] Task 7: Добавить тесты на основные сценарии (`happy path`, `next`, `no results`, `exception fail-soft`) (AC: 1-7)

## Dev Notes

### Developer Context Section

- Story 1.2 продолжает реализованный welcome-flow из Story 1.1 и расширяет его до первого полезного пользовательского результата: показать реальные демо-карточки жилья сразу после первого интента поиска.
- Текущая кодовая база уже содержит: `start` handler (`/start`), callback `try_search`, `AuthMiddleware`, глобальный fail-soft обработчик ошибок в `backend/bot/main.py`; это нужно переиспользовать, а не дублировать.
- Основной пользовательский сценарий для этой story: текстовый запрос или вход через `try_search` → демо-поиск → карточка 1 → кнопочные действия (`Следующая`, `Подробнее`, `Забронировать`, `❤️`) → корректный переход на следующий шаг или fallback.
- Структурный приоритет для MVP: deterministic demo results + state-aware листание в рамках текущего чата; сложный NLP-разбор и production ranking выносятся в последующие stories Epic 3.
- UX-ориентир: “один экран — одно действие”, короткие ответы бота, отсутствие лишних шагов и нулевое трение на старте (без регистрации, без форм, без валидации ПД на этом этапе).

### Technical Requirements

- Использовать `aiogram 3` router/handler паттерн, совместимый с текущей структурой `backend/bot/handlers/*`.
- Входные точки поиска должны работать из двух источников: callback `try_search` и обычное текстовое сообщение пользователя после `/start`.
- Демо-результаты должны формироваться предсказуемо (детерминированный набор), чтобы поведение было тестируемым и воспроизводимым.
- Формат карточки результата в боте должен включать обязательные поля AC: фото (или fallback на placeholder), цена, район, рейтинг.
- Для навигации использовать inline-кнопки с понятными `callback_data` (минимум: `search_next`, `search_details`, `search_book`, `search_favorite`).
- Состояние текущей позиции в выдаче хранить в лёгком state-слое (FSM/контекст или in-memory per-user в рамках текущего процесса) без внедрения новой внешней зависимости.
- Поведение при пустом результате: явный fallback-текст + предложение упростить запрос/перейти к structured flow.
- Все пользовательские ответы строго на русском языке; длина сообщений ограничена для мобильного Telegram UX.
- Любое исключение в search-flow не должно ломать диалог: обработчик возвращает fail-soft сообщение и направляет пользователя к `/start` при необходимости.

### Architecture Compliance

- Соблюдать границы слоёв: bot handlers не должны обращаться к БД напрямую; доступ к данным (если потребуется) через `shared/crud` или сервисный слой.
- Не ломать webhook-архитектуру текущего бота: изменения ограничить обработчиками и регистрацией router, без изменения transport/infra части.
- Переиспользовать существующий global error handling в `backend/bot/main.py`, не создавать дублирующие глобальные ловушки ошибок.
- Не добавлять новые сервисы в `compose.yml` и не вводить новые обязательные переменные окружения для Story 1.2.
- Согласовать поведение с ADR из архитектуры: fast first response в боте, минимальные зависимости, evolution-friendly шаг к FR1-FR3 (Epic 3) без premature optimization.
- Поддерживать принцип “один экран = одно действие”: каждая реакция search-flow должна вести к следующему очевидному действию пользователя.

### Library / Framework Requirements

- Telegram bot слой реализуется на `aiogram 3` (уже используется в проекте); новые обработчики должны следовать текущим паттернам router/message/callback handlers.
- Backend язык и рантайм остаются в Python-стеке проекта; не добавлять сторонние NLP/ML библиотеки для Story 1.2.
- Для тестов использовать текущий `pytest` стек проекта и подход тестирования bot handlers из существующей кодовой базы (`backend/bot/tests/*`).
- Для форматирования/линта придерживаться текущих инструментов проекта (`ruff` для Python), без внедрения новых quality-tool зависимостей.
- Любые helper-структуры для demo search должны быть lightweight и локальными для story, чтобы не создавать долгосрочную архитектурную связность раньше Epic 3.

### File Structure Requirements

- Создать/обновить `backend/bot/handlers/search.py` как основной модуль Story 1.2.
- Обновить `backend/bot/handlers/__init__.py` только если это требуется существующим способом экспорта модулей в проекте.
- Подключить router поиска в `backend/bot/main.py` через `dp.include_router(search.router)`, сохранив текущий порядок инициализации middleware и других router.
- Тесты разместить в `backend/bot/tests/test_search_handler.py` по образцу существующих bot handler тестов.
- Не менять файлы `backend/app/api/routes/*` и `backend/shared/*`, если для demo-search не требуется server-side API.
- Не изменять deployment/infra файлы (`compose.yml`, `compose.override.yml`, Dockerfile*) в рамках Story 1.2.

### Testing Requirements

- Покрыть happy-path: текстовый запрос приводит к показу первой карточки с обязательными полями (фото/цена/район/рейтинг).
- Покрыть callback-path: вход через `try_search` корректно инициирует сценарий и не ломает уже существующий welcome-flow.
- Покрыть навигацию: нажатие `Следующая` последовательно переключает карточки и корректно обрабатывает конец списка.
- Покрыть fallback: пустой результат/невалидный запрос возвращает структурированный ответ с предложением упростить запрос.
- Покрыть fail-soft: исключение в handler не приводит к молчаливому падению, пользователь получает безопасное сообщение.
- Проверить регрессии существующих тестов бота: запуск `backend/bot/tests/*` и отсутствие деградации в `start/welcome/common` сценариях.

### Previous Story Intelligence

- Из Story 1.1 уже реализованы `try_search` callback и RU welcome-тексты; Story 1.2 должна переиспользовать их как входные точки без изменения UX-контракта.
- В предыдущей истории отдельно зафиксирована важность fail-soft поведения; новую search-логику нужно строить в той же модели: всегда отвечать пользователю даже при ошибке.
- В `backend/bot/main.py` уже есть глобальный `on_error`; локальные обработчики search должны дополнять его, а не подменять.
- Повторные пользовательские действия (повторный клик/повторный запрос) в Story 1.1 были признаны важными для UX; search-flow также должен быть идемпотентным и устойчивым к повтору.

### Git Intelligence Summary

- Последний крупный коммит (`06ec6d5`) уже стабилизировал bot-слой: добавлены `welcome` handler, AuthMiddleware, глобальный `on_error`, а также bot unit tests.
- В bot-структуре уже есть устоявшийся паттерн: один feature = отдельный handler-модуль + подключение router в `backend/bot/main.py`; Story 1.2 должна следовать этому же шаблону.
- В кодовой базе нет признаков существующего production-ready search handler в bot-слое; Story 1.2 может безопасно добавить минимальный `search.py` без конфликтов с текущими обработчиками.
- Текущая история изменений указывает на приоритет стабильности и тестов в боте; для Story 1.2 обязательны unit tests на happy/fallback/error ветки до передачи в review.

### Latest Tech Information

- По официальному changelog Telegram, актуальная версия Bot API на момент контекстирования: **9.3** (31 декабря 2025).
- Для Story 1.2 это означает, что базовые методы отправки сообщений/медиа остаются совместимыми с текущим `aiogram 3` подходом проекта, и внедрение нестабильных API-фич не требуется.
- Официальный пакет `aiogram` на PyPI указывает поддержку Telegram Bot API 9.3 и активные релизы ветки 3.x; для этой story рекомендуется оставаться в текущем major/minor стеке проекта без форсированного апгрейда.
- Практический guardrail: избегать использования редких/новых Bot API возможностей (например, потоковых draft-сообщений) в Story 1.2, чтобы сохранить предсказуемость UX и тестов.

### Project Structure Notes

- Изменения концентрируются в bot-слое: `backend/bot/handlers/search.py`, `backend/bot/main.py`, `backend/bot/tests/test_search_handler.py`.
- Именование callback/data и функций должно соответствовать уже существующему стилю `start.py` и `welcome.py` (короткие, явные, action-based идентификаторы).
- Конфликтов с unified project structure не выявлено: Story 1.2 не требует модификации `backend/app` и `backend/shared` для MVP demo-search.

### Project Context Reference

- Файл `project-context.md` в проекте не обнаружен; контекст принят из актуальных planning artifacts (`epics.md`, `architecture.md`, `prd.md`, `ux-design-specification.md`) и текущего состояния bot-кода.
- Если `project-context.md` будет добавлен позже, Story 1.2 следует перепроверить на предмет дополнительных guardrails (особенно naming conventions и UX constraints).

### Story Completion Status

- Story status для документа: `ready-for-dev`.
- Completion note: Ultimate context engine analysis completed - comprehensive developer guide created.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Story 1.2`]
- [Source: `_bmad-output/planning-artifacts/epics.md#Epic 1`]
- [Source: `_bmad-output/planning-artifacts/prd.md#FR8`]
- [Source: `_bmad-output/planning-artifacts/prd.md#FR9`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Bot Framework`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Project Structure & Boundaries`]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md#2.5 Experience Mechanics`]
- [Source: `_bmad-output/implementation-artifacts/1-1-telegram-bot-welcome.md`]
- [Source: `backend/bot/handlers/start.py`]
- [Source: `backend/bot/handlers/welcome.py`]
- [Source: `backend/bot/main.py`]
- [Source: `https://core.telegram.org/bots/api-changelog`]
- [Source: `https://pypi.org/project/aiogram/`]

## Dev Agent Record

### Agent Model Used

GPT-5 Codex CLI

### Debug Log References

- `rg -n` проверки обязательных секций в story файле
- сверка статуса истории в `sprint-status.yaml`
- `UV_CACHE_DIR=/tmp/uv-cache uv run --project backend ruff check backend/bot`
- `UV_CACHE_DIR=/tmp/uv-cache uv run --project backend mypy backend/bot`
- `UV_CACHE_DIR=/tmp/uv-cache uv run --project backend pytest backend/bot/tests -q`

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created
- Story 1.2 подготовлена в статусе `ready-for-dev` с техническими guardrails и тестовыми требованиями
- Scope ограничен demo-search в Telegram-боте без преждевременного расширения в Epic 3 функциональность
- Реализован demo search flow без регистрации: текстовый запрос и кнопка `try_search` запускают показ карточек
- Добавлены последовательный просмотр (Next), actions (Details/Book/Favorite) и fail-soft поведение
- Добавлен fallback для пустых/неподходящих запросов (в т.ч. слишком низкий бюджет)
- Добавлены/обновлены unit tests для search и try_search сценария
- Code-review autofix (2026-02-10): добавлен structured fallback (FR8) с inline-кнопками сценариев при no-results
- Code-review autofix (2026-02-10): усилен fail-soft в callback-ветках `search_details`/`search_book`
- Code-review autofix (2026-02-10): `AuthMiddleware` перенесён на уровень update для единообразной silent-auth обработки callback/update событий

### File List

- `_bmad-output/implementation-artifacts/1-2-demo-search-without-registration.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `backend/bot/handlers/search.py`
- `backend/bot/handlers/welcome.py`
- `backend/bot/handlers/common.py`
- `backend/bot/main.py`
- `backend/bot/tests/test_search_handler.py`
- `backend/bot/tests/test_welcome_handlers.py`

### Change Log

- 2026-02-10: Implemented Story 1.2 demo-search flow in bot, added handlers+tests, updated status to `review`.
- 2026-02-10: Code-review autofix applied (structured no-results fallback + callback fail-soft hardening + middleware scope), status updated to `done`.
