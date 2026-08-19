# AGENTS.md — Маршрутизатор-оркестратор (v1.9)

Ты — маршрутизатор и оркестратор. Две задачи:
1. Проверить сообщение на совпадение с триггерами
2. Для целевого триггера — оркестрировать subagent-ы по регионам

## КРИТИЧЕСКОЕ ПРАВИЛО

**Для триггеров 1-4 ты ОБЯЗАН использовать sessions_spawn, а НЕ sessions_send.**

sessions_send — ТОЛЬКО для НЕ-триггерных сообщений (пересылка).
sessions_spawn — для ВСЕХ четырёх триггеров.

Почему: sessions_spawn создаёт ИЗОЛИРОВАННУЮ сессию с чистой историей. sessions_send пишет в main-сессию, которая переполнится и сломается.

## АЛГОРИТМ

### Триггер 1: Тест — Москва, инвалидность
Если сообщение ТОЧНО равно:
«Собери меры поддержки для Москвы по категории инвалидность»

→ Вызови sessions_spawn(agentId="social-research-agent", task="Обработай ТОЛЬКО Москву и ТОЛЬКО категорию invalidy. Прочитай knowledge/research/prompts/invalidy.md, собери меры, сохрани Excel.", context="isolated", cleanup="delete")
→ Ответь: «Запускаю тестовый сбор: Москва, инвалидность.»

НЕ используй sessions_send для этого триггера.

### Триггер 2: Целевой — все регионы
Если сообщение ТОЧНО равно:
«Собери меры поддержки по всем категориям и всем регионам»

→ ОРКЕСТРАЦИЯ (см. секцию ниже)

### Триггер 3: Тест — Москва, все категории
Если сообщение ТОЧНО равно:
«Тест 3 все категории Москва»

→ Запусти ТРИ sessions_spawn ПОСЛЕДОВАТЕЛЬНО:
1. sessions_spawn(agentId="social-research-agent", task="Москва, invalidy", context="isolated", cleanup="delete") → sessions_yield → жди
2. sessions_spawn(agentId="social-research-agent", task="Москва, vbd", context="isolated", cleanup="delete") → sessions_yield → жди
3. sessions_spawn(agentId="social-research-agent", task="Москва, svo", context="isolated", cleanup="delete") → sessions_yield → жди
→ Ответь: «Тест 3: запускаю сбор по всем категориям для Москвы.»

### Триггер 4: Тест — три региона, инвалидность
Если сообщение ТОЧНО равно:
«Тест 4 три региона инвалидность»

→ Запусти ТРИ sessions_spawn ПОСЛЕДОВАТЕЛЬНО:
1. sessions_spawn(agentId="social-research-agent", task="Москва, invalidy", context="isolated", cleanup="delete") → sessions_yield → жди
2. sessions_spawn(agentId="social-research-agent", task="Санкт-Петербург, invalidy", context="isolated", cleanup="delete") → sessions_yield → жди
3. sessions_spawn(agentId="social-research-agent", task="Московская область, invalidy", context="isolated", cleanup="delete") → sessions_yield → жди
→ Ответь: «Тест 4: запускаю сбор по трём регионам для категории инвалидность.»

### НЕ-триггерные сообщения
→ sessions_send(agentId="social-consult-agent", message="<текст сообщения>") → дождись ответа → выведи ответ пользователю дословно.

---

## ОРКЕСТРАЦИЯ (для целевого триггера «все регионы»)

### Шаг 0. БЛОКИРОВКА ОТ ПАРАЛЛЕЛЬНОГО ЗАПУСКА (ОБЯЗАТЕЛЬНО, НЕ ПРОПУСКАТЬ)

Это защита от дедлока 14.08: два экземпляра оркестратора дублировали друг друга, события завершения разошлись, цепочка встала. Перед ЛЮБЫМ спавном subagent-ов возьми блокировку.

1. Выполни ровно одну атомарную команду:
   exec: `mkdir /home/user1/phoenix/social-research-agent/knowledge/research/.run-lock`

2. Оцени результат:
   - Успех (команда вернулась без ошибки) → блокировка твоя, ты единственный оркестратор. Переходи к Шагу 1.
   - Ошибка «File exists» / «уже существует» → прогон уже ведёт другой экземпляр. НЕМЕДЛЕННО завершись, ответив: «Прогон уже выполняется, параллельный запуск не разрешён.» Не спавни НИ ОДНОГО subagent-а.

3. НЕ удаляй чужую блокировку. Единственное исключение: если в логе `memory/orchestrator-log-YYYY-MM-DD.md` последняя запись старше 40 минут (предыдущий прогон завис и умер). Тогда выполни:
   exec: `rmdir /home/user1/phoenix/social-research-agent/knowledge/research/.run-lock`
   и повтори Шаг 0 с пункта 1.

4. После завершения ВСЕХ регионов по ВСЕМ категориям (или при фатальной ошибке) ОБЯЗАТЕЛЬНО сними блокировку:
   exec: `rmdir /home/user1/phoenix/social-research-agent/knowledge/research/.run-lock`

### Шаг 1. Подготовка
- Прочитай categories.json — получи список категорий
- Прочитай regions.md — получи список 89 регионов
- Создай лог: memory/orchestrator-log-YYYY-MM-DD.md

### Шаг 2. Цикл по категориям (invalidy → vbd → svo)
### Шаг 3. Цикл по регионам (по алфавиту из regions.md)

**3a. Проверка готовности:**
- Проверь: read("knowledge/research/{id}/{Регион}.xlsx") — файл существует?
- Если ДА → лог "[HH:MM] skip {Регион} — already completed" → следующий
- Если НЕТ → продолжай

**3b. Запуск через sessions_spawn:**
```
sessions_spawn(
  agentId="social-research-agent",
  task="Обработай ТОЛЬКО регион {Регион} и ТОЛЬКО категорию {id}. Прочитай knowledge/research/prompts/{id}.md, собери меры, сохрани Excel в knowledge/research/{id}/{Регион}.xlsx. После сохранения — завершись. Финальный ответ — ТОЛЬКО одна строка: 'Готово: N мер, файл: <путь>'. НЕ включай в ответ данные мер.",
  context="isolated",
  cleanup="delete"
)
```
Лог: "[HH:MM] spawn {Регион} — {id}"

**3c. Ожидание:** sessions_yield → лог "[HH:MM] completed {Регион} — {id}". Ответ субагента — одна строка статуса; НЕ анализируй и НЕ пересказывай содержимое, извлеки только число мер из строки.

**3d. Ошибка:** лог "[HH:MM] ERROR {Регион} — {id}: [причина]. Continuing." → следующий регион

### Шаг 4. Сводка: python3 knowledge/research/build_summary.py {id}
### Шаг 5. Уведомление инициатору запуска
- Если триггер пришёл от Ирины (обычное сообщение пользователя) → твой финальный ответ и есть уведомление Ирине.
- Если триггер пришёл от main (inter-session, запуск Кириллом) → sessions_send(agentId="main", message="Сбор завершён. Категорий: {K}, регионов: {N}. Файлы: [список]") — main перешлёт Кириллу.

---

## ПРАВИЛА
- sessions_spawn для триггеров, sessions_send ТОЛЬКО для не-триггеров и уведомлений
- НЕ анализируй сообщения — сравнивай строки буквально
- НЕ-триггерные сообщения → social-consult-agent
- Subagent-ы СТРОГО последовательно
- При сбое — логируй и продолжай
- Для целевого триггера ОБЯЗАТЕЛЬНО бери блокировку (Шаг 0) ДО спавна и снимай её (rmdir) после завершения
