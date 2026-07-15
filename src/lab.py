"""
Лаборатория Истины — SQLite база для отслеживания сигналов (49+ полей)
"""

import sqlite3
import json
import logging
import os
from datetime import datetime
from typing import Optional, Dict, List
from signal_engine import SignalRecord

logger = logging.getLogger(__name__)

class TruthLab:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Инициализировать базу данных с 49+ полями и миграцией reason"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    signal_id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    ticker TEXT,
                    signal_type TEXT,
                    entry_price REAL,
                    stop_loss REAL,
                    take_profit_1 REAL,
                    take_profit_2 REAL,
                    zss_score REAL,
                    rating TEXT,
                    confidence REAL,
                    rsi REAL,
                    macd TEXT,
                    obv TEXT,
                    adx REAL,
                    vwap_diff REAL,
                    bb_position TEXT,
                    stochastic REAL,
                    ichimoku TEXT,
                    weight_rsi REAL,
                    weight_macd REAL,
                    weight_obv REAL,
                    weight_adx REAL,
                    weight_vwap REAL,
                    weight_stochastic REAL,
                    weight_ichimoku REAL,
                    imoex_trend TEXT,
                    sector_trend TEXT,
                    oil_trend TEXT,
                    usd_rur TEXT,
                    cb_rate REAL,
                    level_price REAL,
                    level_age_days INTEGER,
                    level_touches INTEGER,
                    volume_ratio REAL,
                    check_1d_price REAL,
                    check_1d_change REAL,
                    check_3d_price REAL,
                    check_3d_change REAL,
                    check_7d_price REAL,
                    check_7d_change REAL,
                    check_30d_price REAL,
                    check_30d_change REAL,
                    verdict_1d TEXT,
                    verdict_3d TEXT,
                    verdict_7d TEXT,
                    verdict_30d TEXT,
                    reason TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            
            # Миграция: добавить reason если таблица уже существует
            try:
                conn.execute("ALTER TABLE signals ADD COLUMN reason TEXT")
                logger.info("Migration: added 'reason' column to signals")
            except sqlite3.OperationalError:
                pass  # Колонка уже есть

            # Индексы
            conn.execute("CREATE INDEX IF NOT EXISTS idx_signals_ticker ON signals(ticker)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON signals(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_signals_created ON signals(created_at)")
            
            conn.commit()

    def record_signal(self, signal: SignalRecord) -> Optional[str]:
        """Записать сигнал в базу данных"""
        try:
            # Проверка: reason обязателен
            if not signal.reason:
                logger.error("Cannot save signal without 'reason' field")
                return None

            # Сериализовать reason в JSON
            reason_json = json.dumps(signal.reason, ensure_ascii=False)

            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO signals VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                """, (
                    signal.signal_id,
                    signal.timestamp,
                    signal.ticker,
                    signal.signal_type,
                    signal.entry_price,
                    signal.stop_loss,
                    signal.take_profit_1,
                    signal.take_profit_2,
                    signal.zss_score,
                    signal.rating,
                    signal.confidence,
                    signal.rsi,
                    signal.macd,
                    signal.obv,
                    signal.adx,
                    signal.vwap_diff,
                    signal.bb_position,
                    signal.stochastic,
                    signal.ichimoku,
                    signal.weight_rsi,
                    signal.weight_macd,
                    signal.weight_obv,
                    signal.weight_adx,
                    signal.weight_vwap,
                    signal.weight_stochastic,
                    signal.weight_ichimoku,
                    signal.imoex_trend,
                    signal.sector_trend,
                    signal.oil_trend,
                    signal.usd_rur,
                    signal.cb_rate,
                    signal.level_price,
                    signal.level_age_days,
                    signal.level_touches,
                    signal.volume_ratio,
                    signal.check_1d_price,
                    signal.check_1d_change,
                    signal.check_3d_price,
                    signal.check_3d_change,
                    signal.check_7d_price,
                    signal.check_7d_change,
                    signal.check_30d_price,
                    signal.check_30d_change,
                    signal.verdict_1d,
                    signal.verdict_3d,
                    signal.verdict_7d,
                    signal.verdict_30d,
                    reason_json,
                    signal.created_at,
                    signal.updated_at
                ))
                conn.commit()
                logger.info(f"Signal saved: {signal.signal_id}")
                return signal.signal_id

        except Exception as e:
            logger.error(f"Failed to save signal: {e}")
            return None

    def get_signal(self, signal_id: str) -> Optional[Dict]:
        """Получить сигнал по ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM signals WHERE signal_id = ?", (signal_id,)
            ).fetchone()

            if row:
                result = dict(row)
                # Десериализовать reason из JSON
                if result.get('reason'):
                    try:
                        result['reason'] = json.loads(result['reason'])
                    except json.JSONDecodeError:
                        pass
                return result
            return None

    def get_signals_for_outcome_check(self, days_ago: int) -> List[Dict]:
        """
        Получить сигналы для проверки outcomes.
        Сигналы, созданные ровно `days_ago` дней назад.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM signals 
                WHERE date(created_at) = date('now', '-? days')
            """, (days_ago,)).fetchall()

            results = []
            for row in rows:
                result = dict(row)
                if result.get('reason'):
                    try:
                        result['reason'] = json.loads(result['reason'])
                    except json.JSONDecodeError:
                        pass
                results.append(result)
            return results

    def check_signal(self, signal_id: str, current_price: float, days_passed: int) -> Optional[str]:
        """Проверить сигнал и вернуть verdict"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM signals WHERE signal_id = ?", (signal_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            entry_price = row[4]
            change_pct = ((current_price - entry_price) / entry_price) * 100
            
            verdict = "NEUTRAL"
            if change_pct > 2.0:
                verdict = "WIN"
            elif change_pct < -2.0:
                verdict = "LOSS"
            
            # Обновить соответствующее поле verdict
            if days_passed == 1:
                conn.execute("UPDATE signals SET verdict_1d = ?, check_1d_price = ?, check_1d_change = ?, updated_at = ? WHERE signal_id = ?",
                           (verdict, current_price, change_pct, datetime.now().isoformat(), signal_id))
            elif days_passed == 3:
                conn.execute("UPDATE signals SET verdict_3d = ?, check_3d_price = ?, check_3d_change = ?, updated_at = ? WHERE signal_id = ?",
                           (verdict, current_price, change_pct, datetime.now().isoformat(), signal_id))
            elif days_passed == 7:
                conn.execute("UPDATE signals SET verdict_7d = ?, check_7d_price = ?, check_7d_change = ?, updated_at = ? WHERE signal_id = ?",
                           (verdict, current_price, change_pct, datetime.now().isoformat(), signal_id))
            elif days_passed == 30:
                conn.execute("UPDATE signals SET verdict_30d = ?, check_30d_price = ?, check_30d_change = ?, updated_at = ? WHERE signal_id = ?",
                           (verdict, current_price, change_pct, datetime.now().isoformat(), signal_id))
            
            conn.commit()
            return verdict

    def get_stats(self, ticker: Optional[str] = None) -> Dict:
        """Получить статистику сигналов"""
        with sqlite3.connect(self.db_path) as conn:
            if ticker:
                cursor = conn.execute("SELECT verdict_1d FROM signals WHERE ticker = ?", (ticker,))
            else:
                cursor = conn.execute("SELECT verdict_1d FROM signals")
            
            rows = cursor.fetchall()
            
            total = len(rows)
            win = sum(1 for r in rows if r[0] == "WIN")
            loss = sum(1 for r in rows if r[0] == "LOSS")
            neutral = sum(1 for r in rows if r[0] == "NEUTRAL" or r[0] == "pending")
            
            win_rate = (win / total * 100) if total > 0 else 0
            loss_rate = (loss / total * 100) if total > 0 else 0
            
            return {
                "total": total,
                "WIN": win,
                "LOSS": loss,
                "NEUTRAL": neutral,
                "win_rate": round(win_rate, 1),
                "loss_rate": round(loss_rate, 1)
            }

    def recalibrate_weights(self, period_days: int = 30) -> Optional[Dict]:
        """Пересчитать веса на основе статистики (требует >= 10 сигналов)"""
        stats = self.get_stats()
        if stats["total"] < 10:
            return None
        
        # TODO: реализовать логику пересчета весов на основе win_rate
        # Это сложная логика, которая требует анализа корреляций
        # между весами и результатами сигналов
        
        return {"message": "Weight recalibration not yet implemented"}
