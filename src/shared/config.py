"""
Configuration module for the crypto trading bot.
"""

import os
from dataclasses import dataclass, field
from typing import List

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class TradingConfig:
    """Trading parameters."""
    MIN_CONFIDENCE: float = 90.0
    RISK_PER_TRADE: float = 0.02
    STOP_LOSS_PCT: float = 0.02
    TAKE_PROFIT_PCT: float = 0.04
    MAX_OPEN_POSITIONS: int = 5
    SIGNAL_EXPIRY_HOURS: int = 4


@dataclass(frozen=True)
class APIConfig:
    """API credentials and endpoints."""
    SUPABASE_URL: str = field(default_factory=lambda: os.getenv("SUPABASE_URL", ""))
    SUPABASE_KEY: str = field(default_factory=lambda: os.getenv("SUPABASE_KEY", ""))
    BINANCE_API_KEY: str = field(default_factory=lambda: os.getenv("BINANCE_API_KEY", ""))
    BINANCE_SECRET: str = field(default_factory=lambda: os.getenv("BINANCE_SECRET", ""))
    BINANCE_TESTNET: bool = field(default_factory=lambda: os.getenv("BINANCE_TESTNET", "true").lower() == "true")
    OPENAI_API_KEY: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    OPENAI_MODEL: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    TELEGRAM_BOT_TOKEN: str = field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""))
    TELEGRAM_CHAT_ID: str = field(default_factory=lambda: os.getenv("TELEGRAM_CHAT_ID", ""))
    FEAR_GREED_API_URL: str = "https://api.alternative.me/fng/"
    COINGECKO_API_URL: str = "https://api.coingecko.com/api/v3"


@dataclass(frozen=True)
class DataCollectorConfig:
    """Data collector settings."""
    SYMBOLS: tuple = ("BTC/USDT", "ETH/USDT")
    TIMEFRAMES: tuple = ("15m", "1h", "4h")
    CANDLES_LIMIT: int = 100


TRADING = TradingConfig()
API = APIConfig()
DATA_COLLECTOR = DataCollectorConfig()


def validate_config() -> bool:
    """Validate required environment variables."""
    required = {
        "SUPABASE_URL": API.SUPABASE_URL,
        "SUPABASE_KEY": API.SUPABASE_KEY,
        "BINANCE_API_KEY": API.BINANCE_API_KEY,
        "BINANCE_SECRET": API.BINANCE_SECRET,
        "OPENAI_API_KEY": API.OPENAI_API_KEY,
        "TELEGRAM_BOT_TOKEN": API.TELEGRAM_BOT_TOKEN,
        "TELEGRAM_CHAT_ID": API.TELEGRAM_CHAT_ID,
    }

    missing = [name for name, val in required.items() if not val]

    if missing:
        raise ValueError(f"Missing environment variables: {missing}")
    return True
