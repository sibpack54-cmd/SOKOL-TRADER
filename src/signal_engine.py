"""
Signal Engine — генерация сигналов с ZSS scoring
"""

import pytz
import pandas as pd
import numpy as np
import logging
from datetime import datetime, time as dt_time
from typing import Optional, Dict, Tuple
from dataclasses import dataclass

MOSCOW_TZ = pytz.timezone('Europe/Moscow')
MARKET_OPEN = dt_time(10, 0)
MARKET_CLOSE = dt_time(18, 45)

logger = logging.getLogger(__name__)

@dataclass
class SignalRecord:
    signal_id: str
    timestamp: str
    ticker: str
    signal_type: str
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    zss_score: float
    rating: str
    confidence: float
    rsi: float
    macd: str
    obv: str
    adx: float
    vwap_diff: float
    bb_position: str
    stochastic: float
    ichimoku: str
    weight_rsi: float
    weight_macd: float
    weight_obv: float
    weight_adx: float
    weight_vwap: float
    weight_stochastic: float
    weight_ichimoku: float
    imoex_trend: str
    sector_trend: str
    oil_trend: str
    usd_rur: str
    cb_rate: float
    level_price: float
    level_age_days: int
    level_touches: int
    volume_ratio: float
    check_1d_price: float
    check_1d_change: float
    check_3d_price: float
    check_3d_change: float
    check_7d_price: float
    check_7d_change: float
    check_30d_price: float
    check_30d_change: float
    verdict_1d: str
    verdict_3d: str
    verdict_7d: str
    verdict_30d: str
    reason: Dict
    created_at: str
    updated_at: str

class SignalEngine:
    def __init__(self):
        self.last_signal_time: Dict[str, datetime] = {}
        self.attention_budget_counter = 0
        self.last_budget_reset = datetime.now(MOSCOW_TZ)

    def is_market_open(self) -> bool:
        """Проверить, открыта ли биржа"""
        now = datetime.now(MOSCOW_TZ)
        if now.weekday() >= 5:
            return False
        return MARKET_OPEN <= now.time() <= MARKET_CLOSE

    def reset_attention_budget_if_needed(self):
        """Сбросить счетчик attention budget в 00:00 МСК"""
        now = datetime.now(MOSCOW_TZ)
        if now.date() != self.last_budget_reset.date():
            self.attention_budget_counter = 0
            self.last_budget_reset = now

    def check_attention_budget(self, signal_class: str) -> bool:
        """Проверить attention budget (макс 7 actionable сигналов/день)"""
        self.reset_attention_budget_if_needed()
        
        if signal_class in ["A+", "A", "B"]:
            if self.attention_budget_counter >= 7:
                return False
            self.attention_budget_counter += 1
        return True

    def check_duplication(self, ticker: str) -> bool:
        """Проверить дедупликацию (не более 1 сигнала/час на тикер)"""
        if ticker not in self.last_signal_time:
            return True
        
        now = datetime.now(MOSCOW_TZ)
        last_time = self.last_signal_time[ticker]
        
        if (now - last_time).total_seconds() < 3600:
            return False
        
        return True

    def calculate_zss(self, indicators: Dict, signal_type: str) -> Tuple[Optional[float], Optional[float], Optional[Dict]]:
        """
        Рассчитать ZSS (0-5) и Confidence Decomposition.

        Args:
            indicators: dict с ключами rsi, macd, obv, adx, vwap, stoch, bb, ichimoku
            signal_type: BUY или SELL

        Returns:
            (zss_score: float, confidence_pct: float, reason: dict)
            или (None, None, None) если данные некорректны
        """
        required_keys = ['rsi', 'macd', 'obv', 'adx', 'vwap', 'stoch_k', 'bb_upper', 'ichimoku_tenkan']

        # Проверка 1: все ключи на месте
        for key in required_keys:
            if key not in indicators:
                logger.warning(f"Missing indicator: {key}")
                return None, None, None

        # Проверка 2: нет NaN
        values = [indicators[k] for k in required_keys]
        if any(pd.isna(v) or v is None or (isinstance(v, float) and np.isnan(v)) for v in values):
            logger.warning("NaN detected in indicators, skipping ZSS")
            return None, None, None

        # Проверка 3: данные не пустые
        if len([v for v in values if v != 0]) < 4:
            logger.warning("Too few valid indicators for ZSS")
            return None, None, None

        # Расчёт компонентов
        trend_component = min(indicators['adx'] / 50.0, 1.0) * 2.0
        momentum_component = self._calculate_momentum_score(indicators, signal_type)
        volume_component = self._calculate_volume_score(indicators)
        structure_component = self._calculate_structure_score(indicators, signal_type)

        # Проверка 4: компоненты валидны
        components = {
            'trend': trend_component,
            'momentum': momentum_component,
            'volume': volume_component,
            'structure': structure_component
        }

        if any(pd.isna(v) for v in components.values()):
            logger.warning("NaN in ZSS components")
            return None, None, None

        zss_score = sum(components.values())
        zss_score = max(0.0, min(5.0, zss_score))  # clamp 0-5

        confidence_pct = (zss_score / 5.0) * 100.0

        reason = {
            "primary": self._get_primary_reason(components, signal_type),
            "secondary": self._get_secondary_reasons(components, signal_type),
            "contributing": self._get_contributing_indicators(indicators, signal_type),
            "zss_components": components
        }

        return zss_score, confidence_pct, reason

    def _calculate_momentum_score(self, indicators: Dict, signal_type: str) -> float:
        """Рассчитать компонент momentum"""
        rsi = indicators.get('rsi', 50)
        macd_bullish = indicators.get('macd_bullish', False)
        stoch_oversold = indicators.get('stoch_oversold', False)
        stoch_overbought = indicators.get('stoch_overbought', False)

        score = 0.0
        if signal_type == 'BUY':
            if rsi < 30:
                score += 0.5
            if macd_bullish:
                score += 0.3
            if stoch_oversold:
                score += 0.2
        else:  # SELL
            if rsi > 70:
                score += 0.5
            if not macd_bullish:
                score += 0.3
            if stoch_overbought:
                score += 0.2

        return min(score, 1.0)

    def _calculate_volume_score(self, indicators: Dict) -> float:
        """Рассчитать компонент volume"""
        obv_trend = indicators.get('obv_trend', 'unknown')
        volume_ratio = indicators.get('volume_ratio', 1.0)

        score = 0.0
        if obv_trend == 'rising':
            score += 0.3
        if volume_ratio >= 2.0:
            score += 0.7
        elif volume_ratio >= 1.5:
            score += 0.4

        return min(score, 1.0)

    def _calculate_structure_score(self, indicators: Dict, signal_type: str) -> float:
        """Рассчитать компонент structure"""
        bb_position = indicators.get('bb_position', 'middle')
        vwap_diff = indicators.get('vwap_diff', 0)
        ichimoku_position = indicators.get('ichimoku_position', 'unknown')

        score = 0.0
        if signal_type == 'BUY':
            if bb_position == 'lower':
                score += 0.4
            if vwap_diff < -1.0:
                score += 0.3
            if ichimoku_position == 'above_cloud':
                score += 0.3
        else:  # SELL
            if bb_position == 'upper':
                score += 0.4
            if vwap_diff > 1.0:
                score += 0.3
            if ichimoku_position == 'below_cloud':
                score += 0.3

        return min(score, 1.0)

    def _get_primary_reason(self, components: Dict, signal_type: str) -> str:
        """Определить первичную причину сигнала"""
        max_component = max(components.items(), key=lambda x: x[1])
        component_name = max_component[0]
        
        reasons = {
            'trend': 'strong_trend',
            'momentum': 'momentum_shift',
            'volume': 'volume_anomaly',
            'structure': 'structure_break'
        }
        
        return reasons.get(component_name, 'unknown')

    def _get_secondary_reasons(self, components: Dict, signal_type: str) -> list:
        """Определить вторичные причины"""
        secondary = []
        for comp_name, value in components.items():
            if value > 0.5 and comp_name != max(components.items(), key=lambda x: x[1])[0]:
                secondary.append(comp_name)
        return secondary

    def _get_contributing_indicators(self, indicators: Dict, signal_type: str) -> list:
        """Определить индикаторы, способствующие сигналу"""
        contributing = []
        
        if signal_type == 'BUY':
            if indicators.get('rsi', 50) < 30:
                contributing.append('rsi_oversold')
            if indicators.get('macd_bullish', False):
                contributing.append('macd_bullish')
            if indicators.get('obv_trend') == 'rising':
                contributing.append('obv_rising')
            if indicators.get('stoch_oversold', False):
                contributing.append('stochastic_oversold')
        else:
            if indicators.get('rsi', 50) > 70:
                contributing.append('rsi_overbought')
            if not indicators.get('macd_bullish', True):
                contributing.append('macd_bearish')
            if indicators.get('obv_trend') == 'falling':
                contributing.append('obv_falling')
            if indicators.get('stoch_overbought', False):
                contributing.append('stochastic_overbought')
        
        return contributing

    def get_rating(self, zss: float) -> str:
        """Получить рейтинг по ZSS"""
        if zss >= 4.0:
            return "ELITE"
        elif zss >= 3.0:
            return "OPTIMAL"
        elif zss >= 2.0:
            return "MODERATE"
        else:
            return "WEAK"

    def get_signal_class(self, rating: str, volume_ratio: float, has_mega_divergence: bool) -> str:
        """Получить класс события (Voice Guard)"""
        if rating == "ELITE" and volume_ratio >= 3.0 and has_mega_divergence:
            return "A+"
        elif rating == "ELITE" and volume_ratio >= 2.0:
            return "A"
        elif rating == "OPTIMAL":
            return "B"
        else:
            return "C"

    def check_buy_conditions(self, indicators: Dict) -> int:
        """Проверить условия BUY сигнала (возвращает количество выполненных условий)"""
        conditions = 0
        
        if indicators.get("rsi", 50) < 30:
            conditions += 1
        
        if indicators.get("macd_bullish", False):
            conditions += 1
        
        if indicators.get("obv_trend") == "rising":
            conditions += 1
        
        if indicators.get("stoch_oversold", False):
            conditions += 1
        
        if indicators.get("bb_position") == "lower":
            conditions += 1
        
        if indicators.get("ichimoku_position") == "above_cloud":
            conditions += 1
        
        if indicators.get("vwap_diff", 0) < -1.0:
            conditions += 1
        
        return conditions

    def check_sell_conditions(self, indicators: Dict) -> int:
        """Проверить условия SELL сигнала (возвращает количество выполненных условий)"""
        conditions = 0
        
        if indicators.get("rsi", 50) > 70:
            conditions += 1
        
        if not indicators.get("macd_bullish", True):
            conditions += 1
        
        if indicators.get("obv_trend") == "falling":
            conditions += 1
        
        if indicators.get("stoch_overbought", False):
            conditions += 1
        
        if indicators.get("bb_position") == "upper":
            conditions += 1
        
        if indicators.get("ichimoku_position") == "below_cloud":
            conditions += 1
        
        if indicators.get("vwap_diff", 0) > 1.0:
            conditions += 1
        
        return conditions

    def generate_signal(self, indicators: Dict, ticker: str, current_price: float) -> Optional[SignalRecord]:
        """Генерировать сигнал на основе индикаторов"""
        
        # ЭТАП 1: ФИЛЬТРЫ
        if not self.is_market_open():
            return None
        
        if indicators.get("adx", 0) < 20:
            return None  # ТИШИНА В БОКОВИКЕ
        
        if not self.check_duplication(ticker):
            return None
        
        # ЭТАП 2: ПРОВЕРКА УСЛОВИЙ
        buy_conditions = self.check_buy_conditions(indicators)
        sell_conditions = self.check_sell_conditions(indicators)
        
        signal_type = None
        if buy_conditions >= 2:
            signal_type = "BUY"
        elif sell_conditions >= 2:
            signal_type = "SELL"
        
        if not signal_type:
            return None
        
        # ЭТАП 3: ZSS РАСЧЕТ
        zss, confidence, reason = self.calculate_zss(indicators, signal_type)
        
        if zss is None or confidence is None or reason is None:
            logger.warning(f"ZSS calculation failed for {ticker}")
            return None
        
        if zss < 2.0:
            return None  # Слишком слабый сигнал
        
        rating = self.get_rating(zss)
        
        # ЭТАП 4: КЛАСС СОБЫТИЯ
        volume_ratio = 1.0  # TODO: рассчитать реальный volume_ratio
        has_mega_divergence = False  # TODO: реализовать MEGA-DIVERGENCE
        signal_class = self.get_signal_class(rating, volume_ratio, has_mega_divergence)
        
        # ЭТАП 5: ATTENTION BUDGET
        if not self.check_attention_budget(signal_class):
            return None
        
        # ЭТАП 6: РАСЧЕТ ЦЕН
        if signal_type == "BUY":
            entry = current_price * 1.001
            stop_loss = entry * 0.98
            take_profit_1 = entry * 1.02
            take_profit_2 = entry * 1.04
        else:
            entry = current_price * 0.999
            stop_loss = entry * 1.02
            take_profit_1 = entry * 0.98
            take_profit_2 = entry * 0.96
        
        # Записать время последнего сигнала
        self.last_signal_time[ticker] = datetime.now(MOSCOW_TZ)
        
        # Создать SignalRecord
        now = datetime.now(MOSCOW_TZ)
        timestamp = now.isoformat()
        signal_id = f"{ticker}_{timestamp}"
        
        # Extract components from reason for backward compatibility
        zss_components = reason.get('zss_components', {})
        
        return SignalRecord(
            signal_id=signal_id,
            timestamp=timestamp,
            ticker=ticker,
            signal_type=signal_type,
            entry_price=entry,
            stop_loss=stop_loss,
            take_profit_1=take_profit_1,
            take_profit_2=take_profit_2,
            zss_score=round(zss, 2),
            rating=rating,
            confidence=round(confidence, 0),
            rsi=indicators.get("rsi", 0),
            macd=f"{indicators.get('macd', 0):.4f}",
            obv=indicators.get("obv_trend", "unknown"),
            adx=indicators.get("adx", 0),
            vwap_diff=indicators.get("vwap_diff", 0),
            bb_position=indicators.get("bb_position", "middle"),
            stochastic=indicators.get("stoch_k", 50),
            ichimoku=indicators.get("ichimoku_position", "unknown"),
            weight_rsi=zss_components.get('trend', 0) * 20,
            weight_macd=zss_components.get('momentum', 0) * 20,
            weight_obv=zss_components.get('volume', 0) * 20,
            weight_adx=zss_components.get('trend', 0) * 20,
            weight_vwap=zss_components.get('structure', 0) * 20,
            weight_stochastic=zss_components.get('momentum', 0) * 20,
            weight_ichimoku=zss_components.get('structure', 0) * 20,
            imoex_trend="unknown",
            sector_trend="unknown",
            oil_trend="unknown",
            usd_rur="unknown",
            cb_rate=0.0,
            level_price=0.0,
            level_age_days=0,
            level_touches=0,
            volume_ratio=volume_ratio,
            check_1d_price=0.0,
            check_1d_change=0.0,
            check_3d_price=0.0,
            check_3d_change=0.0,
            check_7d_price=0.0,
            check_7d_change=0.0,
            check_30d_price=0.0,
            check_30d_change=0.0,
            verdict_1d="pending",
            verdict_3d="pending",
            verdict_7d="pending",
            verdict_30d="pending",
            reason=reason,
            created_at=timestamp,
            updated_at=timestamp,
        )
