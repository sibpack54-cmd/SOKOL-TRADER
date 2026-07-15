import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    # T-Invest
    TINKOFF_TOKEN = os.getenv("TINKOFF_TOKEN")
    TINKOFF_MODE = os.getenv("TINKOFF_MODE", "sandbox")

    # Таймфрейм
    TIMEFRAME = os.getenv("TIMEFRAME", "15min")

    # Тикеры
    TICKERS = [t.strip() for t in os.getenv("TICKERS", "SBER,GAZP,YNDX,LKOH,ROSN").split(",")]

    # База
    DB_PATH = "data/sokol_lab.db"
    PORTFOLIO_PATH = "data/portfolio.json"
    SETTINGS_PATH = "data/settings.json"

    # Risk
    RISK_PER_TRADE = float(os.getenv("RISK_PER_TRADE", "0.02"))
    CAPITAL = float(os.getenv("CAPITAL", "100000"))

    # API
    TINKOFF_API_URL = "https://invest-public-api.tinkoff.ru/rest"

    # Outcome Engine
    OUTCOME_THRESHOLD_PCT = float(os.getenv("OUTCOME_THRESHOLD_PCT", "2.0"))
    OUTCOME_CHECK_TIME = os.getenv("OUTCOME_CHECK_TIME", "19:00")
    OUTCOME_CHECKPOINTS = [int(x.strip()) for x in os.getenv("OUTCOME_CHECKPOINTS", "1,3,7,30").split(",")]
