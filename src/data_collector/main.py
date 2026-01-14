"""
Data Collector Service Entry Point.
Runs as a Railway cron job every 15 minutes.
"""

import asyncio
from datetime import datetime

from src.shared.config import validate_config, DATA_COLLECTOR
from src.shared.db import DatabaseClient
from src.shared.logger import get_logger
from .binance_client import fetch_ohlcv_data
from .fear_greed import fetch_fear_greed_index
from .coingecko import fetch_coingecko_sentiment

logger = get_logger(__name__)


async def collect_all_data() -> None:
    """Main data collection orchestrator."""
    logger.info("Starting data collection cycle")
    start_time = datetime.utcnow()

    try:
        # Fetch OHLCV data for all configured symbols and timeframes
        for symbol in DATA_COLLECTOR.SYMBOLS:
            for timeframe in DATA_COLLECTOR.TIMEFRAMES:
                candles = await fetch_ohlcv_data(
                    symbol=symbol,
                    timeframe=timeframe,
                    limit=DATA_COLLECTOR.CANDLES_LIMIT,
                )
                if candles:
                    DatabaseClient.insert_candles(candles)

        # Fetch Fear & Greed Index
        fear_greed = await fetch_fear_greed_index()
        if fear_greed:
            DatabaseClient.insert_sentiment(fear_greed)

        # Fetch CoinGecko sentiment for each symbol
        for symbol in DATA_COLLECTOR.SYMBOLS:
            coin_id = symbol.split("/")[0].lower()
            sentiment = await fetch_coingecko_sentiment(coin_id)
            if sentiment:
                DatabaseClient.insert_sentiment(sentiment)

        elapsed = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Data collection completed in {elapsed:.2f}s")

    except Exception as e:
        logger.error(f"Data collection failed: {e}", exc_info=True)
        raise


def main() -> None:
    """Entry point for Railway cron job."""
    validate_config()
    asyncio.run(collect_all_data())


if __name__ == "__main__":
    main()
