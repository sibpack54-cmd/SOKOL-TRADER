# AUDIT REPORT — SOKOL-TRADER v1.0
Дата: 2025-01-17
Версия: v1.0

---

## 🔴 CRITICAL (торговля сломана / деньги под угрозой)

| # | Файл | Строка | Проблема | Fix |
|---|------|--------|----------|-----|
| 1 | `telegram_bot.py` | 20-23 | **Нет whitelist пользователей Telegram** — любой человек может управлять ботом и получать сигналы | Добавить `ALLOWED_CHAT_IDS` в config.py и проверку в каждом handler |
| 2 | `lab.py` | 24 | **SQLite без WAL mode** — при конкурентном доступе (scheduler + telegram) возможны блокировки БД | Добавить `PRAGMA journal_mode=WAL;` после `sqlite3.connect()` |
| 3 | `lab.py` | 24-92 | **Нет thread-safety для SQLite** — `sqlite3.connect()` без блокировок, scheduler запускает concurrent задачи | Использовать `sqlite3.connect(check_same_thread=False)` + `threading.Lock()` или перенести на async SQLite (aiosqlite) |
| 4 | `scheduler.py` | 276-285 | **Нет graceful shutdown для БД** — при SIGTERM/SIGINT не сохраняется состояние, возможна потеря данных | Добавить signal handler (signal.SIGTERM, signal.SIGINT) с сохранением состояния и закрытием соединений |
| 5 | `scheduler.py` | 37-87 | **Portfolio не интегрирован** — `scan_market` генерирует сигналы, но `portfolio.py` не используется, нет реальных позиций | Добавить вызов `portfolio.add_position()` при подтверждении сигнала через Telegram |
| 6 | `portfolio.py` | 46-62 | **Нет мониторинга stop-loss/take-profit** — SL/TP сохраняются в JSON, но нет проверки цен и автозакрытия | Создать отдельную задачу в scheduler для проверки позиций и закрытия при срабатывании SL/TP |
| 7 | `signal_engine.py` | 369-390 | **Нет проверки дублирования позиций** — сигнал может быть сгенерирован для тикера, который уже в портфеле | Добавить проверку `portfolio.get_active_positions()` в `generate_signal()` |
| 8 | `tinkoff_client.py` | 33-69 | **Нет circuit breaker** — при 3+ ошибках API бот продолжает слать запросы, может быть заблокирован | Добавить circuit breaker pattern (отключение на N минут после M ошибок) |
| 9 | `signal_engine.py` | 78-83 | **Упрощённая проверка торгового календаря** — только weekday check, нет учёта праздников Мосбиржи | Интегрировать `pandas_market_calendars` или API Мосбиржи для проверки торговых дней |
| 10 | `tinkoff_client.py` | 1-183 | **Два клиента Tinkoff** — `tinkoff_client.py` (async) и `tinkoff_client_rest.py` (sync) создают путаницу | Удалить `tinkoff_client_rest.py`, использовать только `tinkoff_client.py` (или наоборот) |

---

## 🟠 HIGH (потеря данных / некорректная логика)

| # | Файл | Строка | Проблема | Fix |
|---|------|--------|----------|-----|
| 1 | `telegram_bot.py` | 25-33 | **Не реализованы команды /buy, /sell, /status, /close, /history** — только /start, /radar, /portfolio, /signals, /lab, /settings, /outcomes | Реализовать отсутствующие команды для полного управления портфелем |
| 2 | `telegram_bot.py` | 154-183 | **Нет feedback для долгих операций** — при отправке сигнала бот не отвечает "⏳ Обрабатываю...", может зависнуть на 10+ сек | Добавить `await update.message.reply_text("⏳ Обрабатываю...")` перед долгими операциями |
| 3 | `telegram_bot.py` | 18-33 | **Нет middleware для логирования** — все команды не логируются, невозможно отследить кто что делал | Добавить middleware для логирования всех команд (user_id, command, timestamp) |
| 4 | `telegram_bot.py` | 142-152 | **Нет обработки одновременных команд** — один пользователь может отправить несколько команд подряд, возможны race conditions | Добавить user-specific locks или очередь команд |
| 5 | `docker-compose.yml` | 6-7 | **Неверный путь к Dockerfile** — `context: ..` и `dockerfile: docker/Dockerfile`, но Dockerfile в корне | Исправить на `context: .` и `dockerfile: Dockerfile` |
| 6 | `Dockerfile` | 1-13 | **Нет .dockerignore** — копируются `.venv`, `__pycache__`, `.git`, увеличивает размер образа | Создать `.dockerignore` с исключениями |
| 7 | `docker-compose.yml` | 1-18 | **Нет healthcheck** — если бот упал, Docker не перезапустит его | Добавить `healthcheck` с проверкой процесса |
| 8 | `scheduler.py` | 26-33 | **Нет ротации логов** — `FileHandler` без `RotatingFileHandler`, логи могут вырасти до 10GB | Заменить на `RotatingFileHandler('logs/sokol.log', maxBytes=10MB, backupCount=5)` |
| 9 | `scheduler.py` | 26 | **Нет разделения уровней логов** — везде INFO, в продакшене нужен DEBUG только для разработки | Добавить переменную `LOG_LEVEL` в config.py и использовать её |
| 10 | `install_deps.ps1` | 1-36 | **Только Windows** — нет `install_deps.sh` и `run.sh` для Linux сервера | Создать Linux-аналоги скриптов |
| 11 | `config.py` | 22 | **Жёсткие пути без pathlib** — `"data/sokol_lab.db"` не кроссплатформенно | Использовать `pathlib.Path` для путей |
| 12 | `—` | `—` | **Нет тестов** — нет директории `tests/`, нет pytest coverage | Создать структуру тестов с pytest |
| 13 | `—` | `—` | **Нет mock для T-Invest API** — тесты будут делать реальные запросы | Создать mock для `tinkoff_client` в тестах |
| 14 | `—` | `—` | **Нет интеграционных тестов** — не проверен сценарий покупка → рост → тейк-профит | Добавить end-to-end тесты |
| 15 | `portfolio.py` | 64-77 | **Нет обработки гэпов** — если акция открылась ниже SL, лимитный ордер не исполнится | Использовать рыночный ордер при гэпе ниже SL |
| 16 | `signal_engine.py` | 404-405 | **TODO не реализованы** — `volume_ratio` и `has_mega_divergence` hardcoded | Реализовать расчёт реального volume_ratio и mega-divergence |
| 17 | `lab.py` | 274-284 | **TODO не реализован** — `recalibrate_weights` пустая | Реализовать пересчёт весов на основе статистики |

---

## 🟡 MEDIUM (архитектура / масштабируемость)

| # | Файл | Строка | Проблема | Fix |
|---|------|--------|----------|-----|
| 1 | `Dockerfile` | 1-13 | **Нет multi-stage build** — размер образа может быть >500MB | Использовать multi-stage build для уменьшения размера |
| 2 | `Dockerfile` | 1-13 | **Запуск от root** — контейнер работает от root, небезопасно | Добавить `USER nonroot` после установки зависимостей |
| 3 | `Dockerfile` | 1-13 | **Нет timezone** — время может быть не Moscow Time | Добавить `ENV TZ=Europe/Moscow` и `RUN apt-get update && apt-get install -y tzdata` |
| 4 | `docker-compose.yml` | 13 | **Нет volume для logs/** — логи не персистентны при перезапуске контейнера | Добавить volume для `logs/` |
| 5 | `scheduler.py` | 238-245 | **Интервал сканирования хардкод** — 15 минут в коде, не в конфиге | Вынести `SCAN_INTERVAL_MINUTES` в config.py |
| 6 | `signal_engine.py` | 53-86 | **Сканер не масштабируется** — 5 тикеров × 15 мин = 480 запросов/сутки, на 50 тикеров будет 4800 запросов | Добавить асинхронную загрузку свечей (asyncio.gather) |
| 7 | `indicators.py` | 157-199 | **Индикаторы пересчитываются каждый раз** — нет кеширования, лишняя нагрузка | Добавить кеширование индикаторов с TTL (например, 1 минута) |
| 8 | `tinkoff_client.py` | 22 | **Нет connection pooling** — создаётся новая сессия на каждый запрос | Использовать `aiohttp.TCPConnector(limit=10)` для pooling |
| 9 | `outcome_engine.py` | 306-307 | **Rate limit только 0.5 сек** — при 50 тикерах может превысить лимит API | Добавить адаптивный backoff на основе заголовков rate limit |
| 10 | `scheduler.py` | 270 | **Нет восстановления пропущенных интервалов** — если бот был выключен 2 часа, пропущенные сигналы не обработаются | Добавить логику catch-up при старте |
| 11 | `portfolio.py` | 1-113 | **JSON вместо БД для портфеля** — нет транзакций, возможна потеря данных при краше | Перенести portfolio в SQLite (таблица positions) |
| 12 | `lab.py` | 80-85 | **Миграции через try/except** — нет системы миграций, сложно поддерживать | Использовать Alembic для миграций |
| 13 | `telegram_bot.py` | 179-183 | **Нет форматирования чисел** — цены без разделителей тысяч, сложно читать | Использовать `f"{price:,.2f}"` для форматирования |
| 14 | `telegram_bot.py` | 154-183 | **Нет уведомлений о SL/TP** — при срабатывании стоп-лосса/тейк-профита нет мгновенного сообщения | Добавить webhook или отдельную задачу для немедленных уведомлений |

---

## 🟢 LOW (рефакторинг / оптимизация)

| # | Файл | Строка | Проблема | Fix |
|---|------|--------|----------|-----|
| 1 | `config.py` | 19 | **Тикеры в .env через запятую** — неудобно для большого списка | Использовать JSON-массив или отдельный файл `tickers.json` |
| 2 | `config.py` | 27-28 | **Risk и Capital хардкод** — нет гибкости для разных стратегий | Вынести в отдельный файл `strategy.json` |
| 3 | `signal_engine.py` | 413-422 | **SL/TP хардкод** — 2%/4% в коде, не в конфиге | Вынести `STOP_LOSS_PCT` и `TAKE_PROFIT_PCT` в config.py |
| 4 | `scheduler.py` | 235 | **Timezone хардкод** — "Europe/Moscow" в коде | Вынести `TIMEZONE` в config.py |
| 5 | `telegram_bot.py` | 166 | **Размер позиции хардкод** — "8% капитала" в тексте | Вынести `POSITION_SIZE_PCT` в config.py |
| 6 | `indicators.py` | 12-20 | **RSI без защиты от деления на ноль** — есть, но можно улучшить | Добавить более robust обработку edge cases |
| 7 | `outcome_engine.py` | 220-221 | **Парсинг даты без timezone** — `replace('+00:00', '')` теряет timezone | Использовать `datetime.fromisoformat().astimezone(pytz.UTC)` |
| 8 | `run.ps1` | 19 | **Python не проверяется** — если python не в PATH, упадёт без сообщения | Добавить проверку `where python` |
| 9 | `install_deps.ps1` | 14 | **Redis в зависимостях не используется** — установлен но не используется | Удалить redis из requirements.txt |
| 10 | `requirements.txt` | 9-10 | **Matplotlib/Plotly не используются** — установлены но не используются | Удалить если не планируются графики |

---

## 📋 RECOMMENDATIONS (v1.1)

### Безопасность
- [ ] Добавить PostgreSQL вместо SQLite для продакшена (лучше конкурентный доступ)
- [ ] Добавить 2FA для Telegram бота (дополнительный пин-код)
- [ ] Шифровать токены в БД (если будут храниться)

### Мониторинг
- [ ] Добавить веб-дашборд для мониторинга портфеля (Streamlit/Dash)
- [ ] Интеграция с Grafana/Prometheus для метрик (задержки API, количество сигналов)
- [ ] Добавить Sentry для error tracking

### Масштабируемость
- [ ] Автоматическое масштабирование на 50+ тикеров (asyncio.gather + connection pooling)
- [ ] Добавить Redis для кеширования индикаторов
- [ ] Разделить scanner и executor на разные микросервисы

### Тестирование
- [ ] Покрытие кода тестами >80% (pytest coverage)
- [ ] Интеграционные тесты для всех сценариев
- [ ] Load testing для 50+ тикеров

### Деплой
- [ ] CI/CD через GitHub Actions (тесты → билд Docker → пуш на сервер)
- [ ] Blue-green deployment для нулевого downtime
- [ ] Автоматический бэкап БД (s3 или отдельный volume)

---

## 🚀 DEPLOY-ROADMAP

### Шаг 1: Исправить CRITICAL и HIGH
- [ ] Создать ветку `release/v1.0`
- [ ] Исправить все CRITICAL (10 issues)
- [ ] Исправить все HIGH (17 issues)
- [ ] Написать тесты на исправленные баги

### Шаг 2: Подготовка к Linux деплою
- [ ] Создать `install_deps.sh` и `run.sh` для Linux
- [ ] Оптимизировать Dockerfile (multi-stage, non-root, timezone)
- [ ] Создать `.dockerignore`
- [ ] Исправить `docker-compose.yml` (пути, healthcheck, volumes)

### Шаг 3: Деплой на сервер
- [ ] Подготовить `docker-compose.prod.yml` для Ubuntu 22.04
- [ ] Создать `DEPLOY.md` — пошаговая инструкция:
  ```bash
  git clone → cd → cp .env.example .env → nano .env → 
  docker-compose up -d → проверка логов → готово
  ```

### Шаг 4: CI/CD
- [ ] Настроить GitHub Actions:
  - тесты при push
  - билд Docker при теге
  - деплой на сервер через SSH

---

## ⚠️ ПРАВИЛА РАБОТЫ

- Не менять логику торговли (пороги, интервалы, индикаторы) без подтверждения
- Сначала аудит → потом фиксы → потом деплой
- Каждый fix — отдельный коммит с описанием
- Все изменения — в ветку `release/v1.0`, не в main
- Для каждого бага: файл, строка, описание, fix

---

## 🔍 ПЕРВЫЕ 5 ПРОБЛЕМ (немедленное внимание)

1. **Нет whitelist пользователей Telegram** — любой может управлять ботом
2. **SQLite без WAL mode** — возможны блокировки БД при конкурентном доступе
3. **Нет thread-safety для SQLite** — scheduler запускает concurrent задачи
4. **Portfolio не интегрирован** — сигналы генерируются, но позиции не открываются
5. **Нет мониторинга stop-loss/take-profit** — SL/TP сохраняются, но не проверяются

---

**Аудит завершён. Всего найдено: 10 CRITICAL, 17 HIGH, 14 MEDIUM, 10 LOW.**
