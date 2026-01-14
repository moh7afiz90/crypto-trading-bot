"""
Market condition analyzer.
"""

from dataclasses import dataclass
from typing import Optional

from src.shared.models import TechnicalIndicators
from src.shared.logger import get_logger

logger = get_logger(__name__)


@dataclass
class MarketContext:
    """Preprocessed market context for GPT analysis."""
    trend: str
    rsi_signal: str
    macd_signal: str
    bb_signal: str
    sentiment_signal: str
    summary: str


def analyze_market_conditions(
    indicators: TechnicalIndicators,
    fear_greed_value: Optional[float] = None,
    coingecko_value: Optional[float] = None,
) -> MarketContext:
    """Analyze market conditions and create context for GPT."""

    # Determine trend from SMAs
    trend = "neutral"
    if indicators.sma_20 and indicators.sma_50:
        if indicators.sma_20 > indicators.sma_50:
            trend = "bullish"
        elif indicators.sma_20 < indicators.sma_50:
            trend = "bearish"

    # RSI signal
    rsi_signal = "neutral"
    if indicators.rsi_14:
        if indicators.rsi_14 < 30:
            rsi_signal = "oversold"
        elif indicators.rsi_14 > 70:
            rsi_signal = "overbought"

    # MACD signal
    macd_signal = "neutral"
    if indicators.macd_histogram:
        if indicators.macd_histogram > 0 and indicators.macd_line and indicators.macd_signal:
            if indicators.macd_line > indicators.macd_signal:
                macd_signal = "bullish_cross"
        elif indicators.macd_histogram < 0 and indicators.macd_line and indicators.macd_signal:
            if indicators.macd_line < indicators.macd_signal:
                macd_signal = "bearish_cross"

    # Bollinger Bands signal
    bb_signal = "neutral"
    if indicators.bb_upper and indicators.bb_lower:
        if indicators.current_price <= indicators.bb_lower:
            bb_signal = "oversold"
        elif indicators.current_price >= indicators.bb_upper:
            bb_signal = "overbought"

    # Sentiment signal
    avg_sentiment = None
    if fear_greed_value is not None and coingecko_value is not None:
        avg_sentiment = (fear_greed_value + coingecko_value) / 2
    elif fear_greed_value is not None:
        avg_sentiment = fear_greed_value
    elif coingecko_value is not None:
        avg_sentiment = coingecko_value

    sentiment_signal = "neutral"
    if avg_sentiment is not None:
        if avg_sentiment <= 20:
            sentiment_signal = "extreme_fear"
        elif avg_sentiment <= 40:
            sentiment_signal = "fear"
        elif avg_sentiment >= 80:
            sentiment_signal = "extreme_greed"
        elif avg_sentiment >= 60:
            sentiment_signal = "greed"

    # Create summary
    rsi_str = f"{indicators.rsi_14:.1f}" if indicators.rsi_14 else "N/A"
    sentiment_str = f"{avg_sentiment:.0f}/100" if avg_sentiment else "N/A"

    summary = (
        f"Trend: {trend}. "
        f"RSI: {rsi_str} ({rsi_signal}). "
        f"MACD: {macd_signal}. "
        f"BB: {bb_signal}. "
        f"Sentiment: {sentiment_signal} ({sentiment_str})."
    )

    context = MarketContext(
        trend=trend,
        rsi_signal=rsi_signal,
        macd_signal=macd_signal,
        bb_signal=bb_signal,
        sentiment_signal=sentiment_signal,
        summary=summary,
    )

    logger.info(f"Market context: {summary}")
    return context
