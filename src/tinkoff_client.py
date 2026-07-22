"""
T-Invest REST API Client — замена SDK
"""

import asyncio
import aiohttp
import pandas as pd
from datetime import datetime, timedelta
import logging
from aiohttp import ClientTimeout

from config import Config

logger = logging.getLogger(__name__)

class TinkoffClient:
    def __init__(self):
        self.token = Config.TINKOFF_TOKEN
        self.base_url = Config.TINKOFF_API_URL
        self.figi_cache: dict[str, str] = {}
        self.timeout = ClientTimeout(total=10, connect=5)
        self.session: aiohttp.ClientSession | None = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _request(self, method: str, endpoint: str, body: dict | None = None) -> dict:
        """Выполнить REST API запрос с retry и backoff"""
        url = f"{self.base_url}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        max_retries = 3

        for attempt in range(max_retries):
            try:
                async with self.session.request(method, url, json=body, headers=headers) as response:
                    if response.status == 401:
                        logger.error("❌ Tinkoff API: 401 Unauthorized - проверьте токен")
                        raise ValueError("Invalid Tinkoff token")
                    elif response.status == 429:
                        wait = 2 ** attempt * 60  # 60, 120, 240 сек
                        logger.warning(f"⏳ Rate limit 429, waiting {wait}s...")
                        await asyncio.sleep(wait)
                        continue

                    response.raise_for_status()
                    return await response.json()

            except asyncio.TimeoutError:
                logger.error(f"Timeout on attempt {attempt + 1}/{max_retries}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
            except aiohttp.ClientError as e:
                logger.error(f"HTTP error: {e}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

        raise Exception("Max retries exceeded")

    async def get_figi(self, ticker: str) -> str | None:
        """Получить FIGI по тикеру с кэшированием"""
        ticker = ticker.upper()
        
        if ticker in self.figi_cache:
            return self.figi_cache[ticker]

        try:
            response = await self._request(
                "POST",
                "tinkoff.public.invest.api.contract.v1.InstrumentsService/FindInstrument",
                {"query": ticker, "instrumentType": "share"}
            )

            if response.get("instruments"):
                figi = response["instruments"][0]["figi"]
                self.figi_cache[ticker] = figi
                logger.info(f"✅ FIGI для {ticker}: {figi}")
                return figi
            else:
                logger.warning(f"⚠️ Не найден FIGI для {ticker}")
                return None

        except Exception as e:
            logger.error(f"❌ Ошибка получения FIGI для {ticker}: {e}")
            return None

    async def get_candles(self, ticker: str, interval: str = "15min", days: int = 30) -> pd.DataFrame:
        """
        Загрузить исторические свечи.
        Возвращает DataFrame с колонками: open, high, low, close, volume
        """
        interval_map = {
            "1min": "CANDLE_INTERVAL_1_MIN",
            "5min": "CANDLE_INTERVAL_5_MIN",
            "15min": "CANDLE_INTERVAL_15_MIN",
            "1h": "CANDLE_INTERVAL_HOUR",
            "1d": "CANDLE_INTERVAL_DAY",
        }
        candle_interval = interval_map.get(interval, "CANDLE_INTERVAL_15_MIN")

        figi = await self.get_figi(ticker)
        if not figi:
            logger.error(f"❌ Не найден FIGI для {ticker}")
            return pd.DataFrame()

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        try:
            response = await self._request(
                "POST",
                "tinkoff.public.invest.api.contract.v1.MarketDataService/GetCandles",
                {
                    "figi": figi,
                    "from": start_date.isoformat() + "Z",
                    "to": end_date.isoformat() + "Z",
                    "interval": candle_interval
                }
            )

            candles = []
            for c in response.get("candles", []):
                candles.append({
                    "open": float(c["open"]["units"]) + c["open"]["nano"] / 1e9,
                    "high": float(c["high"]["units"]) + c["high"]["nano"] / 1e9,
                    "low": float(c["low"]["units"]) + c["low"]["nano"] / 1e9,
                    "close": float(c["close"]["units"]) + c["close"]["nano"] / 1e9,
                    "volume": c["volume"],
                    "time": datetime.fromisoformat(c["time"].replace("Z", "+00:00"))
                })

            df = pd.DataFrame(candles)
            if not df.empty:
                df = df.sort_values("time").drop_duplicates(subset=["time"])
                df = df.set_index("time")
                logger.info(f"✅ {ticker}: {len(df)} свечей загружено")

            return df

        except Exception as e:
            logger.error(f"❌ Ошибка загрузки свечей для {ticker}: {e}")
            return pd.DataFrame()

    async def get_current_price(self, ticker: str) -> float:
        """Получить текущую цену"""
        figi = await self.get_figi(ticker)
        if not figi:
            return 0.0

        try:
            response = await self._request(
                "POST",
                "tinkoff.public.invest.api.contract.v1.MarketDataService/GetLastPrices",
                {"figi": [figi]}
            )

            if response.get("lastPrices"):
                price = response["lastPrices"][0]["price"]
                return float(price["units"]) + price["nano"] / 1e9

        except Exception as e:
            logger.error(f"❌ Ошибка получения цены для {ticker}: {e}")

        return 0.0

    async def preload_figis(self, tickers: list[str]):
        """Предзагрузить FIGI для всех тикеров"""
        logger.info("🔄 Предзагрузка FIGI...")
        for ticker in tickers:
            await self.get_figi(ticker)
        logger.info(f"✅ FIGI загружены для {len(self.figi_cache)} тикеров")
