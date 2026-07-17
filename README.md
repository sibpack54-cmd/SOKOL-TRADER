🦅 SOKOL-TRADER v0.5
ZIMA MARKET INTELLIGENCE — Telegram-бот сигналов акций (МосБиржа, Т-Банк Инвестиции)
Философия
«Мы не продаём робота. Мы продаём усиление мышления.»
Бот — советник, не автопилот. Человек решает.
Что работает (v0.5)
✅ T-Invest API (Sandbox / Production)
✅ 5 тикеров: SBER, GAZP, YNDX, LKOH, ROSN
✅ Индикаторы: RSI, MACD, OBV, ADX, VWAP
✅ Telegram-бот: /start, /radar, /portfolio, /lab
✅ Сканер рынка каждые 15 минут
✅ Лаборатория Истины (запись + проверка сигналов)
Быстрый старт
bash
# 1. Клонировать
cd SOKOL-TRADER

# 2. Виртуальное окружение
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Зависимости
pip install -r requirements.txt

# 4. Настройка
cp .env.example .env
# Отредактируй .env: токены Telegram и T-Invest

# 5. Запуск сканера
python src/scheduler.py
Команды Telegram
Table
Команда	Описание
/start	Приветствие
/radar	ТОП-5 возможностей
/portfolio	Мой портфель
/lab	Статистика Лаборатории
Структура
plain
SOKOL-TRADER/
├── src/
│   ├── tinkoff_client.py   # T-Invest API
│   ├── indicators.py       # Технические индикаторы
│   ├── sokol_bot.py        # Telegram-бот
│   ├── scheduler.py        # Планировщик
│   ├── lab.py              # Лаборатория Истины
│   └── config.py           # Настройки
├── data/
│   ├── sokol_lab.db        # База сигналов
│   └── portfolio.json      # Портфель
├── requirements.txt
├── .env.example
└── README.md
Токены
Telegram: @BotFather → /newbot → скопируй token
T-Invest: tinkoff.ru/invest/settings → Токены для OpenAPI → Sandbox
Лицензия
© SOKOL-TRADER — ZIMA MARKET INTELLIGENCE