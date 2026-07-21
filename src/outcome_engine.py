"""
Outcome Engine — проверка результатов сигналов (MFE/MAE, verdicts)
"""

import asyncio
import logging
import sqlite3
from datetime import datetime, timedelta
import pandas as pd

logger = logging.getLogger(__name__)

class OutcomeEngine:
    def __init__(self, lab, client, threshold_pct: float = 2.0):
        """
        Args:
            lab: экземпляр Lab (SQLite)
            client: экземпляр TinkoffClient (aiohttp)
            threshold_pct: порог вердикта в процентах (default 2.0)
        """
        self.lab = lab
        self.client = client
        self.threshold_pct = threshold_pct
        self.checkpoints = [1, 3, 7, 30]

    def init_outcomes_table(self):
        """Создать таблицу outcomes. Вызывать один раз при старте."""
        with sqlite3.connect(self.lab.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS outcomes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signal_id TEXT NOT NULL,
                    checkpoint INTEGER NOT NULL,
                    check_price REAL,
                    entry_price REAL,
                    change_pct REAL,
                    mfe REAL,
                    mae REAL,
                    mfe_pct REAL,
                    mae_pct REAL,
                    verdict TEXT,
                    verdict_reason TEXT,
                    checked_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'PENDING',
                    FOREIGN KEY (signal_id) REFERENCES signals(signal_id) ON DELETE CASCADE,
                    UNIQUE(signal_id, checkpoint)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_outcomes_signal ON outcomes(signal_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_outcomes_status ON outcomes(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_outcomes_verdict ON outcomes(verdict, checkpoint)")
            conn.commit()
            logger.info("Outcomes table initialized")

    async def get_pending_signals(self, checkpoint: int) -> list[dict]:
        """
        Найти сигналы, которым исполнилось `checkpoint` дней,
        и по которым ещё нет проверки.
        """
        with sqlite3.connect(self.lab.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT s.* FROM signals s
                WHERE date(s.created_at) = date('now', '-%d days')
                AND NOT EXISTS (
                    SELECT 1 FROM outcomes o 
                    WHERE o.signal_id = s.signal_id AND o.checkpoint = ?
                )
            """ % checkpoint, (checkpoint,)).fetchall()

            results = []
            for row in rows:
                result = dict(row)
                if result.get('reason'):
                    try:
                        import json
                        result['reason'] = json.loads(result['reason'])
                    except:
                        pass
                results.append(result)

            logger.info(f"Found {len(results)} pending signals for checkpoint {checkpoint}d")
            return results

    async def fetch_candles_for_period(
        self, 
        ticker: str, 
        from_dt: datetime, 
        to_dt: datetime
    ) -> pd.DataFrame | None:
        """
        Получить свечи за период через Tinkoff REST API.

        Returns:
            DataFrame с колонками: time, open, high, low, close, volume
            или None если ошибка
        """
        try:
            # Получить FIGI
            figi = await self.client.get_figi(ticker)
            if not figi:
                logger.error(f"FIGI not found for {ticker}")
                return None

            # Формат дат для API
            from_str = from_dt.isoformat() + "Z"
            to_str = to_dt.isoformat() + "Z"

            # Запрос свечей
            data = await self.client._request(
                "POST", 
                "tinkoff.public.invest.api.contract.v1.MarketDataService/GetCandles",
                json={
                    "figi": figi,
                    "from": from_str,
                    "to": to_str,
                    "interval": "CANDLE_INTERVAL_DAY"  # Дневные свечи для outcomes
                }
            )

            candles = data.get("candles", [])
            if not candles:
                logger.warning(f"No candles for {ticker} in period")
                return None

            df = pd.DataFrame(candles)
            df['time'] = pd.to_datetime(df['time'])
            df['open'] = df['open'].apply(lambda x: float(x.get('units', 0)) + float(x.get('nano', 0)) / 1e9)
            df['high'] = df['high'].apply(lambda x: float(x.get('units', 0)) + float(x.get('nano', 0)) / 1e9)
            df['low'] = df['low'].apply(lambda x: float(x.get('units', 0)) + float(x.get('nano', 0)) / 1e9)
            df['close'] = df['close'].apply(lambda x: float(x.get('units', 0)) + float(x.get('nano', 0)) / 1e9)
            df['volume'] = df['volume']

            return df

        except Exception as e:
            logger.error(f"Failed to fetch candles for {ticker}: {e}")
            return None

    def calculate_mfe_mae(
        self,
        candles: pd.DataFrame,
        entry_price: float,
        signal_type: str
    ) -> tuple[float, float, float, float]:
        """
        Рассчитать MFE и MAE.

        Returns:
            (mfe, mae, mfe_pct, mae_pct)
        """
        if candles.empty or entry_price <= 0:
            return 0.0, 0.0, 0.0, 0.0

        high_max = candles['high'].max()
        low_min = candles['low'].min()

        if signal_type == 'BUY':
            mfe = high_max - entry_price
            mae = entry_price - low_min
        else:  # SELL
            mfe = entry_price - low_min
            mae = high_max - entry_price

        mfe_pct = (mfe / entry_price) * 100.0
        mae_pct = (mae / entry_price) * 100.0

        return mfe, mae, mfe_pct, mae_pct

    def determine_verdict(self, change_pct: float, signal_type: str) -> tuple[str, str]:
        """
        Определить вердикт по правилам.

        Returns:
            (verdict, reason)
        """
        threshold = self.threshold_pct

        if signal_type == 'BUY':
            if change_pct >= threshold:
                return "WIN", f"BUY: +{change_pct:.2f}% >= +{threshold}%"
            elif change_pct <= -threshold:
                return "LOSS", f"BUY: {change_pct:.2f}% <= -{threshold}%"
            else:
                return "NEUTRAL", f"BUY: {change_pct:.2f}% (between -{threshold}% and +{threshold}%)"
        else:  # SELL
            if change_pct <= -threshold:
                return "WIN", f"SELL: {change_pct:.2f}% <= -{threshold}%"
            elif change_pct >= threshold:
                return "LOSS", f"SELL: +{change_pct:.2f}% >= +{threshold}%"
            else:
                return "NEUTRAL", f"SELL: {change_pct:.2f}% (between -{threshold}% and +{threshold}%)"

    async def check_signal(self, signal: dict, checkpoint: int) -> dict | None:
        """
        Проверить один сигнал на одном checkpoint.

        Returns:
            Результат проверки или None если ошибка
        """
        signal_id = signal['signal_id']
        ticker = signal['ticker']
        entry_price = signal['entry_price']
        signal_type = signal['signal_type']
        created_at = signal['created_at']

        logger.info(f"Checking {signal_id} at {checkpoint}d checkpoint")

        # 1. Поставить статус CHECKING
        with sqlite3.connect(self.lab.db_path) as conn:
            conn.execute("""
                INSERT OR IGNORE INTO outcomes (signal_id, checkpoint, status)
                VALUES (?, ?, 'CHECKING')
            """, (signal_id, checkpoint))
            conn.commit()

        try:
            # 2. Определить период
            from_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00').replace('+00:00', ''))
            to_dt = from_dt + timedelta(days=checkpoint)

            # 3. Получить свечи
            candles = await self.fetch_candles_for_period(ticker, from_dt, to_dt)
            if candles is None or candles.empty:
                logger.warning(f"No candles for {signal_id}, skipping")
                return None

            # 4. Цена на момент проверки = close последней свечи
            check_price = candles['close'].iloc[-1]

            # 5. Рассчитать change_pct
            if signal_type == 'BUY':
                change_pct = ((check_price - entry_price) / entry_price) * 100.0
            else:  # SELL
                change_pct = ((entry_price - check_price) / entry_price) * 100.0

            # 6. MFE/MAE
            mfe, mae, mfe_pct, mae_pct = self.calculate_mfe_mae(candles, entry_price, signal_type)

            # 7. Вердикт
            verdict, verdict_reason = self.determine_verdict(change_pct, signal_type)

            # 8. Сохранить результат
            with sqlite3.connect(self.lab.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO outcomes (
                        signal_id, checkpoint, check_price, entry_price, change_pct,
                        mfe, mae, mfe_pct, mae_pct, verdict, verdict_reason, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'COMPLETED')
                """, (
                    signal_id, checkpoint, check_price, entry_price, change_pct,
                    mfe, mae, mfe_pct, mae_pct, verdict, verdict_reason
                ))
                conn.commit()

            result = {
                'signal_id': signal_id,
                'checkpoint': checkpoint,
                'check_price': check_price,
                'change_pct': change_pct,
                'mfe_pct': mfe_pct,
                'mae_pct': mae_pct,
                'verdict': verdict,
                'verdict_reason': verdict_reason
            }

            logger.info(f"Outcome recorded: {signal_id} @ {checkpoint}d = {verdict} ({change_pct:+.2f}%)")
            return result

        except Exception as e:
            logger.error(f"Failed to check {signal_id}: {e}")
            # Вернуть статус в PENDING
            with sqlite3.connect(self.lab.db_path) as conn:
                conn.execute("""
                    UPDATE outcomes SET status = 'PENDING' 
                    WHERE signal_id = ? AND checkpoint = ?
                """, (signal_id, checkpoint))
                conn.commit()
            return None

    async def run_checkpoint(self, checkpoint: int):
        """Проверить все сигналы для одного checkpoint."""
        signals = await self.get_pending_signals(checkpoint)

        if not signals:
            logger.info(f"No pending signals for {checkpoint}d checkpoint")
            return

        logger.info(f"Processing {len(signals)} signals for {checkpoint}d checkpoint")

        processed = 0
        failed = 0

        for signal in signals:
            try:
                result = await self.check_signal(signal, checkpoint)
                if result:
                    processed += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Unexpected error checking signal: {e}")
                failed += 1

            # Небольшая пауза между запросами (rate limit)
            await asyncio.sleep(0.5)

        logger.info(f"Checkpoint {checkpoint}d complete: {processed} processed, {failed} failed")

    async def run_all_checkpoints(self):
        """Проверить все checkpoint'ы последовательно."""
        logger.info("Starting outcome check for all checkpoints")
        for checkpoint in self.checkpoints:
            await self.run_checkpoint(checkpoint)
        logger.info("All outcome checks complete")

    def get_statistics(self) -> dict:
        """Агрегированная статистика по всем outcomes."""
        with sqlite3.connect(self.lab.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Общее количество
            total = conn.execute("SELECT COUNT(DISTINCT signal_id) FROM outcomes WHERE status = 'COMPLETED'").fetchone()[0]

            # По checkpoint'ам
            stats = {"total_signals": total, "by_checkpoint": {}}

            for cp in self.checkpoints:
                rows = conn.execute("""
                    SELECT verdict, COUNT(*) as cnt 
                    FROM outcomes 
                    WHERE checkpoint = ? AND status = 'COMPLETED'
                    GROUP BY verdict
                """, (cp,)).fetchall()

                counts = {"WIN": 0, "LOSS": 0, "NEUTRAL": 0}
                for row in rows:
                    counts[row['verdict']] = row['cnt']

                total_cp = sum(counts.values())
                winrate = (counts["WIN"] / total_cp * 100.0) if total_cp > 0 else 0.0

                stats["by_checkpoint"][cp] = {
                    "win": counts["WIN"],
                    "loss": counts["LOSS"],
                    "neutral": counts["NEUTRAL"],
                    "winrate": winrate
                }

            # MFE/MAE средние
            mfe_row = conn.execute("""
                SELECT AVG(mfe_pct) as avg_mfe, AVG(mae_pct) as avg_mae 
                FROM outcomes WHERE status = 'COMPLETED'
            """).fetchone()

            stats["avg_mfe"] = mfe_row['avg_mfe'] or 0.0
            stats["avg_mae"] = mfe_row['avg_mae'] or 0.0

            return stats
