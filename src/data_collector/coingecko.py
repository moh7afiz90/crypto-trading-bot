"""
CoinGecko API client for sentiment data.
"""

from datetime import datetime
from typing import Optional

import httpx

from src.shared.config import API
from src.shared.models import SentimentData, SentimentSource
from src.shared.logger import get_logger

logger = get_logger(__name__)

COIN_ID_MAP = {
    "btc": "bitcoin",
    "eth": "ethereum",
    "bnb": "binancecoin",
    "sol": "solana",
    "xrp": "ripple",
}


async def fetch_coingecko_sentiment(coin_id: str) -> Optional[SentimentData]:
    """Fetch sentiment data for a specific coin from CoinGecko."""
    cg_coin_id = COIN_ID_MAP.get(coin_id.lower(), coin_id.lower())

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API.COINGECKO_API_URL}/coins/{cg_coin_id}",
                params={
                    "localization": "false",
                    "tickers": "false",
                    "market_data": "true",
                    "community_data": "true",
                    "developer_data": "false",
                },
            )
            response.raise_for_status()
            data = response.json()

        sentiment_votes = data.get("sentiment_votes_up_percentage", 50) or 50
        sentiment_value = min(100, max(0, sentiment_votes))

        if sentiment_value >= 80:
            classification = "Extreme Greed"
        elif sentiment_value >= 60:
            classification = "Greed"
        elif sentiment_value >= 40:
            classification = "Neutral"
        elif sentiment_value >= 20:
            classification = "Fear"
        else:
            classification = "Extreme Fear"

        sentiment = SentimentData(
            source=SentimentSource.COINGECKO,
            symbol=f"{coin_id.upper()}/USDT",
            timestamp=datetime.utcnow(),
            value=sentiment_value,
            classification=classification,
            raw_data={
                "coin_id": cg_coin_id,
                "sentiment_votes_up": sentiment_votes,
                "market_cap_rank": data.get("market_cap_rank"),
                "coingecko_score": data.get("coingecko_score"),
            },
        )

        logger.info(f"CoinGecko sentiment for {coin_id.upper()}: {sentiment_value} ({classification})")
        return sentiment

    except Exception as e:
        logger.error(f"Failed to fetch CoinGecko data for {coin_id}: {e}")
        return None
