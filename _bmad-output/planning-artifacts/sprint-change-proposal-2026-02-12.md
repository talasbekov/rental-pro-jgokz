# Sprint Change Proposal - ReplyKeyboard Navigation & Search Flow

**Дата:** 2026-02-12
**Проект:** rental-pro-jgokz (ЖильеGO)
**Статус:** ✅ Одобрено PO (Erda)
**Категория изменений:** 🟡 Moderate — реорганизация backlog + разработка

---

## 1. Резюме проблемы

### Суть проблемы

Текущая реализация Telegram-бота (Epic 1, Stories 1-2, 1-3, 1-4) не предоставляет постоянного меню навигации и имеет слишком прямолинейный поисковый flow, что снижает usability и противоречит концепции Conversational-First UX с fallback на кнопки.

### Контекст обнаружения

- **Когда:** После завершения Story 1-3 (apartment-card-preview), во время работы над Story 1-4 (basic-navigation)
- **Кто:** Product Owner (Erda)
- **Триггер:** Анализ текущего UX показал отсутствие постоянного доступа к ключевым функциям

### Конкретные проблемы

1. **Отсутствие постоянного меню навигации:**
   - Нет ReplyKeyboard (постоянных кнопок снизу) для быстрого доступа к ключевым функциям
   - Пользователи теряют контекст навигации между действиями
   - Нет быстрого способа вернуться к основным функциям

2. **Слишком прямолинейный поисковый flow:**
   - "Поиск квартир" → сразу карточки квартир (без объяснения)
   - Нет промежуточного шага, объясняющего способы поиска
   - Нет выбора между NLP-поиском (текст) и структурированным поиском (кнопки)

### Влияние на проект

- ⚠️ **UX:** Пользователи теряют контекст, нет постоянного доступа к функциям
- ⚠️ **Conversational-First:** Нарушается принцип "NLP + aggressive fallback на кнопки"
- ⚠️ **Sprint:** Story 1-4 требует полной переработки, Epic 1 растягивается на +2.5-3 дня

### Доказательства

- PRD FR8: "Гость может использовать structured flow (кнопки/меню) как альтернативу NLP"
- UX Spec: "NLP текстовый поиск + aggressive fallback на кнопки"
- Architecture: aiogram 3 поддерживает ReplyKeyboardMarkup нативно

---

## 2. Анализ влияния

### 2.1 Влияние на Epic

| Epic/Story | Текущий статус | Влияние | Требуемые изменения |
|------------|---------------|---------|---------------------|
| **Epic 1** | In-progress (80%) | 🔴 Высокое | Scope расширяется, +2.5-3 дня |
| Story 1-0 | Done | 🟢 Минимальное | Без изменений |
| Story 1-1 | Done | 🟡 Среднее | Добавить настройку ReplyKeyboard при /start |
| Story 1-2 | Done | 🔴 Высокое | Переработать поисковый flow: добавить промежуточный шаг |
| Story 1-3 | Done | 🟢 Минимальное | Интеграция с новым flow, логика карточек без изменений |
| Story 1-4 | In-progress | 🔴 Критическое | **STOP** - полная переработка для ReplyKeyboard |
| **Story 1-1.5 (НОВАЯ)** | — | ➕ Добавить | Реализация ReplyKeyboard menu + обработчики 4 команд |
| Story 1-5 | Backlog | 🟢 Минимальное | Без изменений |
| Epic 2-9 | Backlog | 🟡 Среднее | "Мои бронирования", "Избранные" - заглушки в Epic 1 |

### 2.2 Влияние на артефакты

| Артефакт | Влияние | Конкретные изменения |
|----------|---------|---------------------|
| **PRD** | ✅ Без изменений | Изменения соответствуют FR8 (structured flow fallback) |
| **Architecture** | 🟡 Документация | Добавить секцию "ReplyKeyboard Pattern" в Bot Architecture |
| **UX Specification** | 🟡 Дополнение | Добавить: "Постоянное меню навигации", обновить "Guided first experience" |
| **Epics.md** | 🔴 Изменения | Обновить Story 1-2, 1-4 scope; добавить Story 1-1.5 |
| **sprint-status.yaml** | 🔴 Обновление | ✅ Обновлено: Story 1-4 → backlog; добавлена 1-1.5 |
| **Tests** | 🟡 Расширение | Новые тесты для ReplyKeyboard handlers |

### 2.3 Влияние на будущие Epic

**Epic 3 (Поиск и подбор квартир):**
- Story 3.1 (NLP-поиск) будет интегрироваться с новым промежуточным шагом
- Story 3.2 (Результаты поиска) — без изменений

**Epic 4 (Бронирование и оплата):**
- "Мои бронирования" — новая кнопка в ReplyKeyboard меню
- Нужна заглушка в Epic 1 с сообщением: "Функция появится в Epic 4"

---

## 3. Рекомендуемый путь решения

### Выбранный подход: Direct Adjustment (Прямая корректировка)

**Суть:**
- Модификация существующих Stories 1-2, 1-4
- Добавление новой Story 1-1.5
- Без отката завершенных Stories

### Обоснование выбора

**Преимущества:**
1. ✅ **Минимальные усилия:** 2.5-3 дня vs альтернатив
2. ✅ **Низкий технический риск:** ReplyKeyboard — стандартная функция aiogram 3
3. ✅ **Улучшает продукт:**
   - Постоянный доступ к ключевым функциям
   - Соответствие Conversational-First UX
   - Лучшая guided experience для новых пользователей
4. ✅ **Сохраняет momentum:** команда продолжает Epic 1, моральный дух высокий
5. ✅ **Соответствует PRD:** усиливает FR8 (structured flow как альтернатива NLP)

**Рассмотренные альтернативы:**

| Вариант | Оценка | Причина отклонения |
|---------|--------|-------------------|
| **Откат (Rollback)** | ❌ Not viable | Потеря 4 завершенных stories, высокий риск демотивации, усилия выше чем forward fix |
| **MVP Review** | ❌ Not viable | Избыточно, MVP не под угрозой, изменения улучшают продукт, а не расширяют scope |

**Trade-offs:**
- ➖ Epic 1 растягивается на +2.5-3 дня
- ➖ Story 1-4 требует переработки (sunk cost ~8-12 часов работы)
- ➕ Долгосрочная выгода: лучший UX, меньше технического долга
- ➕ Aligned с PRD vision и UX спецификацией

---

## 4. Детальный план изменений

### 4.1 Влияние на MVP

- ✅ **MVP достижим:** изменения не блокируют запуск
- ⚠️ **Timeline:** Epic 1 +2.5-3 дня (с 8 недель общего MVP → ~8.5 недель)
- ✅ **Scope:** не расширяется, улучшается качество существующих требований
- ✅ **Критерии готовности:** не меняются

### 4.2 Требуемые изменения по Stories

#### Story 1-1.5 (НОВАЯ): Reply Keyboard Persistent Menu

**Статус:** Backlog → Ready-for-dev
**Приоритет:** P0 (блокирует 1-2 и 1-4)
**Усилия:** 6-8 часов

**Описание:**
Реализовать постоянное меню навигации (ReplyKeyboardMarkup) с 4 кнопками, доступными на всех экранах бота.

**Кнопки:**
1. 🔍 **Поиск квартир** — запуск поискового flow
2. 📋 **Мои бронирования** — просмотр истории (заглушка для Epic 4)
3. ❤️ **Избранные** — избранные квартиры (заглушка для Epic 3)
4. 🧹 **Очистить переписку** — очистка истории чата

**Acceptance Criteria:**
1. ReplyKeyboard настраивается при /start и /help
2. Все 4 кнопки всегда видны пользователю
3. Обработчики для каждой кнопки реализованы
4. "Мои бронирования" и "Избранные" показывают заглушку: "Функция появится в следующих epic"
5. "Очистить переписку" удаляет историю сообщений в чате
6. Тесты покрывают все handlers

**Файлы:**
- `backend/bot/keyboards/reply.py` — ReplyKeyboardMarkup builder
- `backend/bot/handlers/common.py` — обработчики постоянных команд
- `backend/bot/tests/test_reply_keyboard.py` — новые тесты

---

#### Story 1-2 (UPDATE): Demo Search - Intermediate Step

**Статус:** Done → Ready-for-dev (update)
**Приоритет:** P0 (зависит от 1-1.5)
**Усилия:** 4-6 часов

**Описание:**
Добавить промежуточный шаг после нажатия "Поиск квартир", где пользователь получает инструкцию и выбирает способ поиска.

**Изменения:**
1. После нажатия "🔍 Поиск квартир" (ReplyKeyboard):
   - Отправить инструкцию: "Я помогу найти квартиру! Выберите удобный способ:"
   - Показать inline-кнопки:
     - "🔍 Написать что ищу" (NLP текстовый поиск)
     - "📋 Выбрать по параметрам" (структурированный поиск кнопками)

2. State management для промежуточного состояния

3. При выборе "Написать что ищу" → переход к существующему NLP flow

4. При выборе "Выбрать по параметрам" → структурированный flow (кнопки для города, дат, бюджета)

**Acceptance Criteria:**
1. Промежуточный шаг отображается после "Поиск квартир"
2. Пользователь видит инструкцию и 2 способа поиска
3. Выбор "Написать что ищу" → NLP flow работает как раньше
4. Выбор "Выбрать по параметрам" → структурированный flow
5. State корректно управляется
6. Обновлены существующие тесты

**Файлы:**
- `backend/bot/handlers/search.py` — обновить search flow
- `backend/bot/tests/test_search_handler.py` — обновить тесты

---

#### Story 1-4 (REWRITE): Basic Navigation - ReplyKeyboard Integration

**Статус:** In-progress → Backlog → Ready-for-dev (rewrite)
**Приоритет:** P1 (зависит от 1-1.5 и 1-2)
**Усилия:** 8-12 часов

**Описание:**
Полная переработка навигации для интеграции с ReplyKeyboard. Удалить старую inline-навигацию, использовать ReplyKeyboard как основную навигацию.

**Изменения:**
1. **Удалить** старую inline-навигацию (если она конфликтует)
2. **Интегрировать** ReplyKeyboard как основную навигацию
3. **Контекстные inline-кнопки** остаются для действий в карточках:
   - "Подробнее", "Забронировать", "❤️ В избранное" — в карточках квартир
   - "Следующая", "Назад к поиску" — навигация по результатам
4. **Structured flow** (кнопки для выбора параметров поиска)

**Acceptance Criteria:**
1. ReplyKeyboard доступен на всех экранах
2. Контекстные inline-кнопки работают в карточках
3. Структурированный поисковый flow реализован (город → даты → бюджет → результаты)
4. Навигация по результатам поиска работает ("Следующая", "Назад")
5. Все существующие тесты обновлены
6. Регрессионное тестирование Stories 1-0, 1-1, 1-3 пройдено

**Файлы:**
- `backend/bot/handlers/search.py` — structured flow
- `backend/bot/keyboards/inline.py` — контекстные кнопки
- `backend/bot/tests/test_search_handler.py` — переписать тесты

---

### 4.3 Implementation Sequence

**Фаза 1: Остановка и планирование (0.5 дня)**
1. ⏸️ **STOP** работа над Story 1-4
2. 📋 Создать детальные спецификации для Stories 1-1.5, 1-2, 1-4
3. 🔄 ✅ sprint-status.yaml обновлен

**Фаза 2: Реализация (2 дня)**
1. **Day 1:** Story 1-1.5 (ReplyKeyboard menu) — 6-8 часов
2. **Day 1-2:** Story 1-2 (Intermediate step) — 4-6 часов
3. **Day 2:** Story 1-4 (Navigation rewrite) — 8-12 часов

**Фаза 3: Интеграция и тестирование (0.5 дня)**
1. ✅ Регрессионное тестирование Stories 1-0, 1-1, 1-3
2. 🧪 E2E тест полного flow: /start → ReplyKeyboard → поиск → карточка → бронирование
3. 📝 Обновить user documentation

**Итого:** ~20-26 часов (2.5-3 дня разработки)

**Dependencies:**
```
Story 1-1.5 (ReplyKeyboard)
    ↓
Story 1-2 (Intermediate step)
    ↓
Story 1-4 (Navigation rewrite)
    ↓
Epic 1 завершение
```

---

## 5. План передачи и ответственность

### 5.1 Категория изменений

🟡 **Moderate** — требуется реорганизация backlog + разработка

### 5.2 Ответственные роли

| Роль | Агент | Ответственность | Workflow |
|------|-------|----------------|----------|
| **Development Team** | bmad-agent-bmm-dev | Реализация Stories 1-1.5, 1-2 (update), 1-4 (rewrite) | `/bmad-bmm-dev-story` для каждой story |
| **Scrum Master** | bmad-agent-bmm-sm | ✅ sprint-status.yaml обновлен, управление backlog, координация | Manual sprint-status update |
| **Product Owner** | Erda | ✅ Утверждение одобрено, приоритизация, приемка stories | Review & approve каждую story |

### 5.3 Handoff Deliverables

**Для Dev Agent:**
- ✅ Детальные спецификации Stories 1-1.5, 1-2, 1-4 (в этом документе)
- ✅ Acceptance Criteria для каждой story
- ✅ Примеры ReplyKeyboard layout:
  ```python
  # backend/bot/keyboards/reply.py
  from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

  def get_main_menu() -> ReplyKeyboardMarkup:
      return ReplyKeyboardMarkup(
          keyboard=[
              [KeyboardButton(text="🔍 Поиск квартир")],
              [KeyboardButton(text="📋 Мои бронирования"), KeyboardButton(text="❤️ Избранные")],
              [KeyboardButton(text="🧹 Очистить переписку")]
          ],
          resize_keyboard=True,
          persistent=True
      )
  ```
- ✅ Ссылки: [aiogram 3 ReplyKeyboard docs](https://docs.aiogram.dev/en/latest/api/types/reply_keyboard_markup.html)

**Для SM Agent:**
- ✅ sprint-status.yaml обновлен
- ✅ Timeline estimate: +2.5-3 дня
- ✅ Dependency graph Stories

**Для PO (Erda):**
- ✅ Sprint Change Proposal document (этот документ)
- ✅ Одобрение получено
- 📬 Notification при готовности каждой story к review

### 5.4 Success Criteria

**Для завершения Sprint Change:**
- ✅ Sprint Change Proposal утвержден PO
- ✅ sprint-status.yaml обновлен
- ✅ Stories 1-1.5, 1-2, 1-4 имеют четкие AC
- ✅ Dev Agent готов к выполнению

**Для приемки Stories:**
- ✅ Все AC выполнены
- ✅ Тесты проходят (coverage ≥80%)
- ✅ Регрессионное тестирование пройдено
- ✅ Code review завершен

---

## 6. Следующие шаги

### Немедленные действия:

1. ✅ **Sprint Change Proposal одобрен** — Erda
2. ✅ **sprint-status.yaml обновлен** — SM Agent
3. 📋 **Создать Story 1-1.5** — Dev Agent
   ```bash
   /bmad-bmm-create-story
   # Story ID: 1-1.5-reply-keyboard-persistent-menu
   ```

4. 🔨 **Начать разработку Story 1-1.5** — Dev Agent
   ```bash
   /bmad-bmm-dev-story 1-1.5-reply-keyboard-persistent-menu
   ```

### Последовательность выполнения:

```
Week Current (Feb 12-16):
  Day 1: Story 1-1.5 (ReplyKeyboard) → 6-8 hours
  Day 2: Story 1-2 UPDATE (Intermediate step) → 4-6 hours
  Day 3: Story 1-4 REWRITE (Navigation) → 8-12 hours
  Day 3-4: Testing & Integration → 4 hours

Week Next (Feb 17-):
  Story 1-5 (Landing page) → proceed as planned
  Epic 1 завершение
```

### Коммуникация:

- 📬 Dev Agent → PO: уведомление при готовности каждой story к review
- 📊 SM Agent → Team: обновление sprint progress после каждой story
- ✅ PO → Dev Agent: приемка story после review

---

## 7. Итоговая оценка

### Резюме изменений

| Аспект | До изменения | После изменения |
|--------|-------------|----------------|
| **Навигация** | Только inline кнопки в контексте | ReplyKeyboard + контекстные inline кнопки |
| **Поисковый flow** | "Поиск" → сразу карточки | "Поиск" → инструкция + выбор способа → карточки |
| **UX соответствие** | Частичное (нет постоянного меню) | Полное (Conversational-First + fallback) |
| **Epic 1 timeline** | ~6 дней (оригинал) | ~8.5-9 дней (+2.5-3 дня) |
| **MVP timeline** | ~8 недель | ~8.5 недель (+0.5 недели) |
| **Технический долг** | Средний (неполная навигация) | Низкий (complete UX implementation) |

### Ключевые преимущества

1. ✅ **Улучшенный UX:** постоянный доступ к ключевым функциям
2. ✅ **Соответствие PRD:** усиливает Conversational-First с fallback на кнопки
3. ✅ **Guided experience:** промежуточный шаг объясняет способы поиска
4. ✅ **Низкий риск:** стандартные функции aiogram, без новых технологий
5. ✅ **Долгосрочная выгода:** меньше технического долга, лучшая поддерживаемость

### Риски и митигация

| Риск | Вероятность | Влияние | Митигация |
|------|------------|---------|-----------|
| Задержка разработки | Средняя | Средняя | Четкие AC, детальные спецификации, Dev Agent с опытом |
| Регрессия в Stories 1-0 до 1-3 | Низкая | Средняя | Регрессионное тестирование обязательно |
| Конфликт с Epic 3 (NLP) | Низкая | Низкая | Промежуточный шаг подготовлен для NLP интеграции |

---

## 8. Приложения

### A. Примеры кода

**ReplyKeyboard layout:**
```python
# backend/bot/keyboards/reply.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu() -> ReplyKeyboardMarkup:
    """Постоянное меню навигации (4 кнопки)"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Поиск квартир")],
            [
                KeyboardButton(text="📋 Мои бронирования"),
                KeyboardButton(text="❤️ Избранные")
            ],
            [KeyboardButton(text="🧹 Очистить переписку")]
        ],
        resize_keyboard=True,
        persistent=True,  # Остается видимым на всех экранах
        input_field_placeholder="Выберите действие или напишите сообщение..."
    )
```

**Промежуточный шаг поиска:**
```python
# backend/bot/handlers/search.py
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

@router.message(F.text == "🔍 Поиск квартир")
async def on_search_start(message: Message):
    """Промежуточный шаг: инструкция + выбор способа поиска"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Написать что ищу", callback_data="search_nlp")],
        [InlineKeyboardButton(text="📋 Выбрать по параметрам", callback_data="search_structured")]
    ])

    await message.answer(
        "Я помогу найти квартиру! 🏠\n\n"
        "Выберите удобный способ:\n"
        "• Напишите текстом что ищете\n"
        "• Или выберите параметры по шагам",
        reply_markup=keyboard
    )
```

### B. Ссылки

- **PRD:** [prd.md](prd.md#FR8) — FR8 (structured flow fallback)
- **Architecture:** [architecture.md](architecture.md#bot-architecture) — Bot Architecture
- **UX Spec:** [ux-design-specification.md](ux-design-specification.md#conversational-first) — Conversational-First UX
- **Epic 1:** [epics.md](epics.md#epic-1) — Первое касание и знакомство с продуктом
- **aiogram 3 Docs:** [ReplyKeyboardMarkup](https://docs.aiogram.dev/en/latest/api/types/reply_keyboard_markup.html)

### C. Checklist для Dev Agent

**Story 1-1.5 (ReplyKeyboard):**
- [ ] Создать `backend/bot/keyboards/reply.py`
- [ ] Реализовать `get_main_menu()` function
- [ ] Обработчики для 4 команд в `backend/bot/handlers/common.py`
- [ ] Настройка ReplyKeyboard при /start и /help
- [ ] Заглушки для "Мои бронирования" и "Избранные"
- [ ] Реализовать "Очистить переписку"
- [ ] Написать тесты `backend/bot/tests/test_reply_keyboard.py`
- [ ] Все тесты проходят (coverage ≥80%)

**Story 1-2 (Intermediate step):**
- [ ] Обновить `backend/bot/handlers/search.py`
- [ ] Добавить промежуточный шаг с инструкцией
- [ ] Inline-кнопки: "Написать что ищу" / "Выбрать по параметрам"
- [ ] State management для промежуточного состояния
- [ ] Интеграция с существующим NLP flow
- [ ] Обновить `backend/bot/tests/test_search_handler.py`
- [ ] Все тесты проходят

**Story 1-4 (Navigation rewrite):**
- [ ] Удалить конфликтующую inline-навигацию
- [ ] Интегрировать ReplyKeyboard как основную навигацию
- [ ] Контекстные inline-кнопки в карточках
- [ ] Structured flow (город → даты → бюджет)
- [ ] Навигация по результатам ("Следующая", "Назад")
- [ ] Переписать тесты
- [ ] Регрессионное тестирование Stories 1-0, 1-1, 1-3
- [ ] E2E тест полного flow

---

**Документ подготовлен:** Correct Course Workflow
**Версия:** 1.0
**Дата одобрения:** 2026-02-12
**Статус:** ✅ Approved & Ready for Implementation
