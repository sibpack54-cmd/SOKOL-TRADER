#!/bin/bash
# SOKOL-TRADER — установка зависимостей (Linux)
# Запускать из папки проекта: bash install_deps.sh

echo "🦅 SOKOL-TRADER — установка зависимостей"

# Проверяем виртуальное окружение
if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ Активируй venv: source venv/bin/activate"
    exit 1
fi

# Базовые зависимости
echo "📦 Установка базовых зависимостей..."
pip install pandas numpy python-telegram-bot apscheduler python-dotenv pytz aiohttp matplotlib plotly

# Tinkoff Investments
echo "📦 Установка T-Invest API..."

# Способ 1: PyPI
pip install tinkoff-investments
if [ $? -eq 0 ]; then
    echo "✅ Tinkoff установлен с PyPI"
else
    echo "⚠️ PyPI не работает, пробуем GitHub..."

    # Способ 2: GitHub
    pip install git+https://github.com/Tinkoff/invest-python.git
    if [ $? -eq 0 ]; then
        echo "✅ Tinkoff установлен с GitHub"
    else
        echo "❌ Tinkoff не установлен. Будем использовать REST API."
    fi
fi

echo "🚀 Готово! Проверь: python -c 'import pandas; import telegram'"
