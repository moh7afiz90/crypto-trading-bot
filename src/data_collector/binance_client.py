"""
Binance OHLCV data fetcher using CCXT.
"""

from datetime import datetime
from typing import List, Optional

import ccxt.async_support as ccxt

from src.shared.config import API
from src.shared.models import OHLCVCandle
from src.shared.logger import get_logger

logger = get_logger(__name__)


async def fetch_ohlcv_data(
    symbol: str, timeframe: str = "15m", limit: int = 100
) -> Optional[List[OHLCVCandle]]:
    """Fetch OHLCV candle data from Binance."""
    exchange = ccxt.binance(
        {
            "apiKey": API.BINANCE_API_KEY,
            "secret": API.BINANCE_SECRET,
            "enableRateLimit": True,
        }
    )

    if API.BINANCE_TESTNET:
        exchange.set_sandbox_mode(True)

    try:
        logger.info(f"Fetching {limit} {timeframe} candles for {symbol}")

        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

        candles = []
        for candle in ohlcv:
            timestamp, open_price, high, low, close, volume = candle
            candles.append(
                OHLCVCandle(
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=datetime.utcfromtimestamp(timestamp / 1000),
                    open=open_price,
                    high=high,
                    low=low,
                    close=close,
                    volume=volume,
                )
            )

        logger.info(f"Fetched {len(candles)} candles for {symbol}")
        return candles

    except Exception as e:
        logger.error(f"Failed to fetch OHLCV for {symbol}: {e}")
        return None

    finally:
        await exchange.close()
