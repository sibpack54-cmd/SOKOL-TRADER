"""
Технические индикаторы
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """RSI(14) с защитой от деления на ноль"""
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rs = rs.replace([np.inf, -np.inf], 100).fillna(50)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(df: pd.DataFrame, fast=12, slow=26, signal=9) -> Tuple[pd.Series, pd.Series, pd.Series, bool]:
    """MACD(12, 26, 9)"""
    ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line
    is_bullish = macd.iloc[-1] > signal_line.iloc[-1]
    return macd, signal_line, histogram, is_bullish

def calculate_obv(df: pd.DataFrame) -> Tuple[pd.Series, str]:
    """OBV"""
    obv = (np.sign(df["close"].diff()) * df["volume"]).fillna(0).cumsum()
    trend = "rising" if obv.iloc[-1] > obv.iloc[-5] else "falling"
    return obv, trend

def calculate_adx(df: pd.DataFrame, period: int = 14) -> Tuple[float, float, float, str]:
    """ADX(14) с защитой от недостатка данных"""
    if len(df) < 28:
        return 0.0, 0.0, 0.0, "unknown"
    
    high = df["high"]
    low = df["low"]
    close = df["close"]

    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    atr = tr.rolling(period).mean()

    up = high - high.shift()
    down = low.shift() - low

    plus_dm = up.where((up > down) & (up > 0), 0)
    minus_dm = down.where((down > up) & (down > 0), 0)

    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr)

    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(period).mean().fillna(0)

    trend = "bullish" if plus_di.iloc[-1] > minus_di.iloc[-1] else "bearish"

    return adx.iloc[-1], plus_di.iloc[-1], minus_di.iloc[-1], trend

def calculate_vwap(df: pd.DataFrame) -> Tuple[float, float]:
    """VWAP за текущий торговый день"""
    if df.empty:
        return 0.0, 0.0
    
    today = df.index[-1].date()
    df_today = df[df.index.date == today]
    
    if df_today.empty:
        return 0.0, 0.0
    
    vwap = (df_today["volume"] * (df_today["high"] + df_today["low"] + df_today["close"]) / 3).sum() / df_today["volume"].sum()
    last_close = df["close"].iloc[-1]
    diff_pct = ((last_close - vwap) / vwap) * 100 if vwap > 0 else 0.0
    
    return vwap, diff_pct

def calculate_stochastic(df: pd.DataFrame, k_period=14, d_period=3, smooth=3) -> Tuple[float, float, bool, bool]:
    """Stochastic(14, 3, 3)"""
    if len(df) < k_period + d_period + smooth:
        return 50.0, 50.0, False, False
    
    lowest_low = df["low"].rolling(k_period).min()
    highest_high = df["high"].rolling(k_period).max()
    
    k = 100 * (df["close"] - lowest_low) / (highest_high - lowest_low)
    k = k.fillna(50)
    d = k.rolling(d_period).mean().fillna(50)
    
    k_value = k.iloc[-1]
    d_value = d.iloc[-1]
    is_oversold = k_value < 20
    is_overbought = k_value > 80
    
    return k_value, d_value, is_oversold, is_overbought

def calculate_bollinger_bands(df: pd.DataFrame, period=20, std_dev=2) -> Tuple[float, float, float, str, float]:
    """Bollinger Bands(20, 2)"""
    if len(df) < period:
        return 0.0, 0.0, 0.0, "middle", 0.0
    
    sma = df["close"].rolling(period).mean()
    std = df["close"].rolling(period).std()
    
    upper = sma + std_dev * std
    lower = sma - std_dev * std
    last_close = df["close"].iloc[-1]
    
    if last_close < lower.iloc[-1]:
        position = "lower"
    elif last_close > upper.iloc[-1]:
        position = "upper"
    else:
        position = "middle"
    
    bandwidth = ((upper.iloc[-1] - lower.iloc[-1]) / sma.iloc[-1]) * 100 if sma.iloc[-1] > 0 else 0.0
    
    return upper.iloc[-1], lower.iloc[-1], sma.iloc[-1], position, bandwidth

def calculate_ichimoku(df: pd.DataFrame, tenkan=9, kijun=26, senkou=52) -> Tuple[float, float, str]:
    """Ichimoku(9, 26, 52)"""
    if len(df) < senkou + 26:
        return 0.0, 0.0, "unknown"
    
    high = df["high"]
    low = df["low"]
    
    tenkan_sen = (high.rolling(tenkan).max() + low.rolling(tenkan).min()) / 2
    kijun_sen = (high.rolling(kijun).max() + low.rolling(kijun).min()) / 2
    
    senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(26)
    senkou_span_b = ((high.rolling(senkou).max() + low.rolling(senkou).min()) / 2).shift(26)
    
    cloud_top = pd.concat([senkou_span_a, senkou_span_b], axis=1).max(axis=1)
    cloud_bottom = pd.concat([senkou_span_a, senkou_span_b], axis=1).min(axis=1)
    
    last_close = df["close"].iloc[-1]
    
    if last_close > cloud_top.iloc[-1]:
        position = "above_cloud"
    elif last_close < cloud_bottom.iloc[-1]:
        position = "below_cloud"
    else:
        position = "inside_cloud"
    
    return tenkan_sen.iloc[-1], kijun_sen.iloc[-1], position

def get_indicators(df: pd.DataFrame) -> Dict:
    """Получить все индикаторы для последней свечи"""
    if df.empty or len(df) < 30:
        return {}

    try:
        rsi = calculate_rsi(df).iloc[-1]
        macd, macd_signal, macd_hist, macd_bullish = calculate_macd(df)
        obv, obv_trend = calculate_obv(df)
        adx, plus_di, minus_di, adx_trend = calculate_adx(df)
        vwap, vwap_diff = calculate_vwap(df)
        stoch_k, stoch_d, stoch_oversold, stoch_overbought = calculate_stochastic(df)
        bb_upper, bb_lower, bb_sma, bb_position, bb_bandwidth = calculate_bollinger_bands(df)
        ichimoku_tenkan, ichimoku_kijun, ichimoku_position = calculate_ichimoku(df)

        return {
            "rsi": round(rsi, 1),
            "macd": round(macd.iloc[-1], 4),
            "macd_signal": round(macd_signal.iloc[-1], 4),
            "macd_bullish": macd_bullish,
            "obv_trend": obv_trend,
            "adx": round(adx, 1),
            "plus_di": round(plus_di, 1),
            "minus_di": round(minus_di, 1),
            "adx_trend": adx_trend,
            "vwap_diff": round(vwap_diff, 2),
            "stoch_k": round(stoch_k, 1),
            "stoch_d": round(stoch_d, 1),
            "stoch_oversold": stoch_oversold,
            "stoch_overbought": stoch_overbought,
            "bb_upper": round(bb_upper, 2),
            "bb_lower": round(bb_lower, 2),
            "bb_sma": round(bb_sma, 2),
            "bb_position": bb_position,
            "bb_bandwidth": round(bb_bandwidth, 2),
            "ichimoku_tenkan": round(ichimoku_tenkan, 2),
            "ichimoku_kijun": round(ichimoku_kijun, 2),
            "ichimoku_position": ichimoku_position,
            "close": df["close"].iloc[-1],
        }
    except Exception as e:
        logger.error(f"❌ Ошибка расчета индикаторов: {e}")
        return {}
