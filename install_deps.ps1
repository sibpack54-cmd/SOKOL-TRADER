# SOKOL-TRADER — установка зависимостей (Windows PowerShell)
# Запускать из папки проекта: .\install_deps.ps1

Write-Host "🦅 SOKOL-TRADER — установка зависимостей" -ForegroundColor Cyan

# Проверяем виртуальное окружение
if (-not $env:VIRTUAL_ENV) {
    Write-Host "❌ Активируй venv: .\venv\Scripts\Activate.ps1" -ForegroundColor Red
    exit 1
}

# Базовые зависимости (без tinkoff — его отдельно)
Write-Host "📦 Установка базовых зависимостей..." -ForegroundColor Yellow
pip install pandas numpy python-telegram-bot apscheduler python-dotenv pytz aiohttp redis matplotlib plotly

# Tinkoff Investments (пробуем разные способы)
Write-Host "📦 Установка T-Invest API..." -ForegroundColor Yellow

# Способ 1: PyPI
pip install tinkoff-investments
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Tinkoff установлен с PyPI" -ForegroundColor Green
} else {
    Write-Host "⚠️ PyPI не работает, пробуем GitHub..." -ForegroundColor Yellow

    # Способ 2: GitHub
    pip install git+https://github.com/Tinkoff/invest-python.git
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Tinkoff установлен с GitHub" -ForegroundColor Green
    } else {
        Write-Host "❌ Tinkoff не установлен. Будем использовать REST API." -ForegroundColor Red
        Write-Host "   Создадим fallback-клиент (tinkoff_client_rest.py)" -ForegroundColor Yellow
    }
}

Write-Host "🚀 Готово! Проверь: python -c 'import pandas; import telegram'" -ForegroundColor Green