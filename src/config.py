import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    # === Telegram ===
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    ALLOWED_CHAT_IDS = [int(id.strip()) for id in os.getenv("ALLOWED_CHAT_IDS", "").split(",") if id.strip()]

    # === T-Invest API ===
    TINKOFF_TOKEN = os.getenv("TINKOFF_TOKEN")
    TINKOFF_MODE = os.getenv("TINKOFF_MODE", "sandbox")
    TINKOFF_API_URL = "https://invest-public-api.tinkoff.ru/rest"

    # === Trading ===
    TIMEFRAME = os.getenv("TIMEFRAME", "15min")
    TICKERS = [t.strip() for t in os.getenv("TICKERS", "SBER,GAZP,YNDX,LKOH,ROSN").split(",")]

    # === Risk Management ===
    RISK_PER_TRADE = float(os.getenv("RISK_PER_TRADE", "0.02"))
    CAPITAL = float(os.getenv("CAPITAL", "100000"))  # RUB

    # === Database (SQLite) ===
    DB_PATH = str(Path(__file__).parent.parent / "data" / "sokol_lab.db")
    PORTFOLIO_PATH = str(Path(__file__).parent.parent / "data" / "portfolio.json")
    SETTINGS_PATH = str(Path(__file__).parent.parent / "data" / "settings.json")

    # === Outcome Engine ===
    OUTCOME_THRESHOLD_PCT = float(os.getenv("OUTCOME_THRESHOLD_PCT", "2.0"))
    OUTCOME_CHECK_TIME = os.getenv("OUTCOME_CHECK_TIME", "19:00")
    OUTCOME_CHECKPOINTS = [int(x.strip()) for x in os.getenv("OUTCOME_CHECKPOINTS", "1,3,7,30").split(",")]

    # === System ===
    TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # === Validation ===
    @classmethod
    def validate(cls):
        missing = []
        if not cls.TELEGRAM_TOKEN:
            missing.append("TELEGRAM_TOKEN")
        if not cls.TINKOFF_TOKEN:
            missing.append("TINKOFF_TOKEN")
        if not cls.ALLOWED_CHAT_IDS:
            missing.append("ALLOWED_CHAT_IDS")
        if missing:
            raise ValueError(f"Missing required env variables: {', '.join(missing)}")
        return True
    