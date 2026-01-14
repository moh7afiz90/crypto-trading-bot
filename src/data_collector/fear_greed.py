"""
Alternative.me Fear & Greed Index API client.
"""

from datetime import datetime
from typing import Optional

import httpx

from src.shared.config import API
from src.shared.models import SentimentData, SentimentSource
from src.shared.logger import get_logger

logger = get_logger(__name__)


async def fetch_fear_greed_index() -> Optional[SentimentData]:
    """Fetch current Fear & Greed Index from Alternative.me."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                API.FEAR_GREED_API_URL, params={"limit": 1, "format": "json"}
            )
            response.raise_for_status()
            data = response.json()

        if not data.get("data"):
            logger.warning("No Fear & Greed data returned")
            return None

        fng_data = data["data"][0]
        value = int(fng_data["value"])
        classification = fng_data["value_classification"]
        timestamp = datetime.utcfromtimestamp(int(fng_data["timestamp"]))

        sentiment = SentimentData(
            source=SentimentSource.FEAR_GREED,
            symbol=None,
            timestamp=timestamp,
            value=value,
            classification=classification,
            raw_data=fng_data,
        )

        logger.info(f"Fear & Greed Index: {value} ({classification})")
        return sentiment

    except Exception as e:
        logger.error(f"Failed to fetch Fear & Greed Index: {e}")
        return None
