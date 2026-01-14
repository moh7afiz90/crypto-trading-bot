"""
Analysis Agent Service Entry Point.
Runs as a Railway cron job every 15 minutes (after data collector).
"""

import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Optional

from src.shared.config import validate_config, TRADING, DATA_COLLECTOR
from src.shared.db import DatabaseClient
from src.shared.models import SignalCreate, SignalType, TechnicalIndicators
from src.shared.indicators import calculate_all_indicators
from src.shared.logger import get_logger
from .analyzer import analyze_market_conditions
from .openai_client import get_gpt_analysis

logger = get_logger(__name__)


def _calculate_bb_position(indicators: TechnicalIndicators) -> Optional[str]:
    """Calculate position relative to Bollinger Bands."""
    if not all([indicators.bb_upper, indicators.bb_lower, indicators.current_price]):
        return None

    price = indicators.current_price
    if price >= indicators.bb_upper:
        return "above_upper"
    elif price <= indicators.bb_lower:
        return "below_lower"
    else:
        return "within_bands"


async def generate_signals() -> None:
    """Main signal generation orchestrator."""
    logger.info("Starting analysis cycle")
    start_time = datetime.utcnow()

    try:
        for symbol in DATA_COLLECTOR.SYMBOLS:
            # Get recent candle data
            candles = DatabaseClient.get_candles(
                symbol=symbol, timeframe="15m", limit=100
            )

            if not candles or len(candles) < 50:
                logger.warning(f"Insufficient data for {symbol}")
                continue

            # Extract prices (oldest first for indicator calculation)
            prices = [float(c["close"]) for c in reversed(candles)]
            current_price = prices[-1]
            timestamp = datetime.utcnow()

            # Calculate technical indicators
            indicators = calculate_all_indicators(symbol, prices, timestamp)

            # Get sentiment data
            fear_greed = DatabaseClient.get_latest_sentiment("fear_greed")
            coingecko = DatabaseClient.get_latest_sentiment("coingecko", symbol)

            # Prepare market context for GPT
            market_context = analyze_market_conditions(
                indicators=indicators,
                fear_greed_value=float(fear_greed["value"]) if fear_greed else None,
                coingecko_value=float(coingecko["value"]) if coingecko else None,
            )

            # Get GPT analysis
            analysis = await get_gpt_analysis(
                symbol=symbol, indicators=indicators, market_context=market_context
            )

            if not analysis:
                logger.warning(f"No analysis returned for {symbol}")
                continue

            # Only create signals at 90%+ confidence
            if analysis.should_trade and analysis.confidence >= TRADING.MIN_CONFIDENCE:
                entry_price = current_price

                if analysis.signal_type == SignalType.BUY:
                    stop_loss = entry_price * (1 - TRADING.STOP_LOSS_PCT)
                    take_profit = entry_price * (1 + TRADING.TAKE_PROFIT_PCT)
                else:
                    stop_loss = entry_price * (1 + TRADING.STOP_LOSS_PCT)
                    take_profit = entry_price * (1 - TRADING.TAKE_PROFIT_PCT)

                signal = SignalCreate(
                    symbol=symbol,
                    signal_type=analysis.signal_type,
                    confidence=Decimal(str(analysis.confidence)),
                    entry_price=Decimal(str(entry_price)),
                    stop_loss_price=Decimal(str(stop_loss)),
                    take_profit_price=Decimal(str(take_profit)),
                    analysis_summary=analysis.reasoning,
                    technical_data={
                        "rsi": indicators.rsi_14,
                        "sma_20": indicators.sma_20,
                        "sma_50": indicators.sma_50,
                        "macd": indicators.macd_histogram,
                        "bb_position": _calculate_bb_position(indicators),
                        "fear_greed": fear_greed["value"] if fear_greed else None,
                        "key_factors": analysis.key_factors,
                    },
                )

                DatabaseClient.create_signal(signal)
                logger.info(
                    f"Created {analysis.signal_type} signal for {symbol} "
                    f"at {entry_price:.2f} with {analysis.confidence}% confidence"
                )
            else:
                logger.info(
                    f"No signal for {symbol}: "
                    f"should_trade={analysis.should_trade}, "
                    f"confidence={analysis.confidence}%"
                )

        elapsed = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Analysis cycle completed in {elapsed:.2f}s")

    except Exception as e:
        logger.error(f"Analysis cycle failed: {e}", exc_info=True)
        raise


def main() -> None:
    """Entry point for Railway cron job."""
    validate_config()
    asyncio.run(generate_signals())


if __name__ == "__main__":
    main()
