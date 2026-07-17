# DEPLOY — SOKOL-TRADER v1.0

## Требования

- Ubuntu 22.04 (или другой Linux с Docker)
- Docker 20.10+
- Docker Compose 2.0+
- Git

## Шаг 1: Клонирование репозитория

```bash
git clone <repository-url>
cd SOKOL-TRADER-v1.0
```

## Шаг 2: Настройка переменных окружения

```bash
cp .env.example .env
nano .env
```

Заполните следующие переменные:

```
# Telegram
TELEGRAM_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
ALLOWED_CHAT_IDS=123456789

# T-Invest API
TINKOFF_TOKEN=your_tinkoff_api_token
TINKOFF_MODE=sandbox  # или production для реальной торговли

# Настройки
TIMEFRAME=15min
TICKERS=SBER,GAZP,YNDX,LKOH,ROSN
RISK_PER_TRADE=0.02
CAPITAL=100000

# Outcome Engine
OUTCOME_THRESHOLD_PCT=2.0
OUTCOME_CHECK_TIME=19:00
OUTCOME_CHECKPOINTS=1,3,7,30
```

**Важно:** Получите ваш Telegram chat_id:
1. Откройте @userinfobot в Telegram
2. Отправьте /start
3. Получите ваш chat_id и добавьте в ALLOWED_CHAT_IDS

## Шаг 3: Создание директорий

```bash
mkdir -p data logs
chmod 755 data logs
```

## Шаг 4: Сборка Docker образа

```bash
docker-compose build
```

## Шаг 5: Запуск

```bash
docker-compose up -d
```

## Шаг 6: Проверка логов

```bash
docker-compose logs -f
```

Ожидаемый вывод:
```
sokol-trader  | 🦅 SOKOL-TRADER v0.6.2 запускается...
sokol-trader  | ===================================================
sokol-trader  | 📁 База данных: data/sokol_lab.db
sokol-trader  | 📈 Тикеры: SBER, GAZP, YNDX, LKOH, ROSN
sokol-trader  | ⏱️  Таймфрейм: 15min
sokol-trader  | 🎯 Порог Outcome: ±2.0%
sokol-trader  | 🔍 Загрузка FIGI...
sokol-trader  | ✅ FIGI загружены
sokol-trader  | 🤖 Telegram Bot инициализирован
sokol-trader  | 🕐 Сканер: каждые 15 минут
sokol-trader  | 🕐 Проверка позиций: каждые 5 минут
sokol-trader  | 🕐 Outcome check: ежедневно в 19:00 МСК
sokol-trader  | ===================================================
sokol-trader  | ✅ SOKOL-TRADER v0.6.2 работает!
sokol-trader  | 💡 Нажмите Ctrl+C для остановки
```

## Шаг 7: Проверка Telegram бота

Отправьте `/start` боту в Telegram. Если всё настроено правильно, бот ответит.

## Управление

**Просмотр логов:**
```bash
docker-compose logs -f
```

**Остановка:**
```bash
docker-compose down
```

**Перезапуск:**
```bash
docker-compose restart
```

**Обновление:**
```bash
git pull
docker-compose down
docker-compose build
docker-compose up -d
```

## Команды Telegram бота

- `/start` — приветствие и справка
- `/radar` — ТОП-5 возможностей
- `/portfolio` — текущий портфель с P&L
- `/signals` — активные сигналы
- `/lab` — статистика Лаборатории Истины
- `/outcomes` — статистика результатов
- `/buy <ticker> <lots>` — ручная покупка
- `/sell <ticker>` — ручная продажа
- `/status` — статус позиций
- `/close <ticker>` — закрытие позиции по рынку

## Траблшутинг

**Бот не отвечает:**
1. Проверьте логи: `docker-compose logs -f`
2. Убедитесь, что TELEGRAM_TOKEN правильный
3. Убедитесь, что ваш chat_id в ALLOWED_CHAT_IDS

**Ошибки API T-Invest:**
1. Проверьте TINKOFF_TOKEN
2. Убедитесь, что TINKOFF_MODE правильный (sandbox/production)
3. Проверьте лимиты API (sandbox: 300 запросов/мин, production: 100 запросов/мин)

**Проблемы с БД:**
1. Проверьте права доступа к директории `data/`
2. Убедитесь, что директория существует: `ls -la data/`

**Контейнер падает:**
1. Проверьте healthcheck: `docker inspect sokol-trader`
2. Проверьте логи: `docker-compose logs`
3. Перезапустите: `docker-compose restart`

## Резервное копирование

**Бэкап БД:**
```bash
cp data/sokol_lab.db data/sokol_lab.db.backup.$(date +%Y%m%d)
```

**Бэкап портфеля:**
```bash
cp data/portfolio.json data/portfolio.json.backup.$(date +%Y%m%d)
```

**Автоматический бэкап (cron):**
```bash
# Добавить в crontab: crontab -e
0 2 * * * cd /path/to/SOKOL-TRADER-v1.0 && cp data/sokol_lab.db data/sokol_lab.db.backup.$(date +\%Y\%m\%d)
```

## Безопасность

- Никогда не коммитить `.env` в Git
- Использовать сильные токены
- Ограничить ALLOWED_CHAT_IDS только доверенным пользователям
- Регулярно обновлять зависимости
- Использовать firewall для ограничения доступа к серверу

## Мониторинг

**Проверка статуса контейнера:**
```bash
docker ps
```

**Проверка использования ресурсов:**
```bash
docker stats sokol-trader
```

**Проверка дискового пространства:**
```bash
df -h
du -sh data/ logs/
```

## Поддержка

При проблемах:
1. Проверьте логи: `docker-compose logs -f`
2. Посмотрите AUDIT_REPORT.md
3. Создайте issue в репозитории
