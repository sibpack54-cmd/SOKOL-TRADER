"""
Tinkoff REST API Client — fallback если SDK не установлен
Использует openapi.tinkoff.ru напрямую через requests
"""

import os
import requests
import pandas as pd
from datetime import datetime, timedelta

class TinkoffRestClient:
    """REST API клиент для T-Invest (fallback)"""

    BASE_URL = "https://invest-public-api.tinkoff.ru/rest"

    def __init__(self, token=None):
        self.token = token or os.getenv("TINKOFF_TOKEN")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def _get(self, endpoint, params=None):
        url = f"{self.BASE_URL}/{endpoint}"
        response = requests.get(url, headers=self.headers, params=params, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ API Error {response.status_code}: {response.text[:200]}")
            return None

    def find_instrument(self, ticker):
        """Найти инструмент по тикеру"""
        data = self._get("tinkoff.public.invest.api.contract.v1.InstrumentsService/FindInstrument", 
                        {"query": ticker})
        if data and "instruments" in data:
            for inst in data["instruments"]:
                if inst.get("ticker") == ticker and inst.get("instrumentType") == "share":
                    return inst
        return None

    def get_figi(self, ticker):
        """Получить FIGI по тикеру"""
        inst = self.find_instrument(ticker)
        return inst.get("figi") if inst else None

    def get_candles(self, ticker, interval="15min", days=7):
        """Получить свечи"""
        figi = self.get_figi(ticker)
        if not figi:
            print(f"❌ FIGI не найден для {ticker}")
            return pd.DataFrame()

        # Интервалы: 1min, 5min, 15min, hour, day
        interval_map = {
            "1min": "CANDLE_INTERVAL_1_MIN",
            "5min": "CANDLE_INTERVAL_5_MIN", 
            "15min": "CANDLE_INTERVAL_15_MIN",
            "1h": "CANDLE_INTERVAL_HOUR",
            "1d": "CANDLE_INTERVAL_DAY"
        }

        end = datetime.now()
        start = end - timedelta(days=days)

        body = {
            "figi": figi,
            "from": start.isoformat() + "Z",
            "to": end.isoformat() + "Z",
            "interval": interval_map.get(interval, "CANDLE_INTERVAL_15_MIN")
        }

        url = f"{self.BASE_URL}/tinkoff.public.invest.api.contract.v1.MarketDataService/GetCandles"
        response = requests.post(url, headers=self.headers, json=body, timeout=30)

        if response.status_code != 200:
            print(f"❌ Ошибка загрузки свечей: {response.status_code}")
            return pd.DataFrame()

        data = response.json()
        candles = data.get("candles", [])

        if not candles:
            return pd.DataFrame()

        rows = []
        for c in candles:
            rows.append({
                "open": self._parse_price(c.get("open", {})),
                "high": self._parse_price(c.get("high", {})),
                "low": self._parse_price(c.get("low", {})),
                "close": self._parse_price(c.get("close", {})),
                "volume": c.get("volume", 0),
                "time": c.get("time", "")
            })

        df = pd.DataFrame(rows)
        if not df.empty:
            df["time"] = pd.to_datetime(df["time"])
            df = df.sort_values("time").set_index("time")
            print(f"✅ {ticker}: {len(df)} свечей загружено")

        return df

    def get_current_price(self, ticker):
        """Получить текущую цену"""
        figi = self.get_figi(ticker)
        if not figi:
            return 0.0

        url = f"{self.BASE_URL}/tinkoff.public.invest.api.contract.v1.MarketDataService/GetLastPrices"
        response = requests.post(url, headers=self.headers, json={"figi": [figi]}, timeout=30)

        if response.status_code == 200:
            data = response.json()
            prices = data.get("lastPrices", [])
            if prices:
                return self._parse_price(prices[0].get("price", {}))

        return 0.0

    def _parse_price(self, price_obj):
        """Парсинг цены из JSON"""
        if not price_obj:
            return 0.0
        units = price_obj.get("units", 0)
        nano = price_obj.get("nano", 0)
        return float(units) + float(nano) / 1e9


# Патч для совместимости с оригинальным tinkoff_client.py
try:
    from tinkoff.invest import Client
    TinkoffClient = None  # Используем оригинальный
except ImportError:
    # SDK не установлен — используем REST fallback
    TinkoffClient = TinkoffRestClient
    print("⚠️ Tinkoff SDK не найден. Используем REST API fallback.")