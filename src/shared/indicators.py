"""
Technical analysis indicator calculations.
"""

from datetime import datetime
from typing import List, Optional, Tuple

import numpy as np

from .models import TechnicalIndicators
from .logger import get_logger

logger = get_logger(__name__)


def calculate_sma(prices: List[float], period: int) -> Optional[float]:
    """Calculate Simple Moving Average."""
    if len(prices) < period:
        return None
    return float(np.mean(prices[-period:]))


def calculate_ema(prices: List[float], period: int) -> Optional[float]:
    """Calculate Exponential Moving Average."""
    if len(prices) < period:
        return None

    multiplier = 2 / (period + 1)
    ema = prices[0]

    for price in prices[1:]:
        ema = (price * multiplier) + (ema * (1 - multiplier))

    return float(ema)


def calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
    """Calculate Relative Strength Index."""
    if len(prices) < period + 1:
        return None

    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return float(rsi)


def calculate_macd(
    prices: List[float],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """Calculate MACD."""
    if len(prices) < slow_period + signal_period:
        return None, None, None

    fast_ema = calculate_ema(prices, fast_period)
    slow_ema = calculate_ema(prices, slow_period)

    if fast_ema is None or slow_ema is None:
        return None, None, None

    macd_line = fast_ema - slow_ema

    macd_values = []
    for i in range(slow_period - 1, len(prices)):
        subset = prices[:i + 1]
        fast = calculate_ema(subset, fast_period)
        slow = calculate_ema(subset, slow_period)
        if fast and slow:
            macd_values.append(fast - slow)

    if len(macd_values) < signal_period:
        return macd_line, None, None

    signal_line = calculate_ema(macd_values, signal_period)
    histogram = macd_line - signal_line if signal_line else None

    return macd_line, signal_line, histogram


def calculate_bollinger_bands(
    prices: List[float],
    period: int = 20,
    std_dev: float = 2.0
) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """Calculate Bollinger Bands."""
    if len(prices) < period:
        return None, None, None

    recent_prices = prices[-period:]
    middle_band = float(np.mean(recent_prices))
    std = float(np.std(recent_prices))

    upper_band = middle_band + (std_dev * std)
    lower_band = middle_band - (std_dev * std)

    return upper_band, middle_band, lower_band


def calculate_all_indicators(
    symbol: str,
    prices: List[float],
    timestamp: datetime
) -> TechnicalIndicators:
    """Calculate all technical indicators for a symbol."""
    current_price = prices[-1] if prices else 0

    rsi = calculate_rsi(prices, 14)
    sma_20 = calculate_sma(prices, 20)
    sma_50 = calculate_sma(prices, 50)
    macd_line, macd_signal, macd_hist = calculate_macd(prices)
    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(prices)

    indicators = TechnicalIndicators(
        symbol=symbol,
        timestamp=timestamp,
        rsi_14=rsi,
        sma_20=sma_20,
        sma_50=sma_50,
        macd_line=macd_line,
        macd_signal=macd_signal,
        macd_histogram=macd_hist,
        bb_upper=bb_upper,
        bb_middle=bb_middle,
        bb_lower=bb_lower,
        current_price=current_price
    )

    logger.debug(f"Indicators for {symbol}: RSI={rsi}, SMA20={sma_20}")
    return indicators
