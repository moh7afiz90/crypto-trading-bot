"""
Pytest configuration and shared fixtures.
"""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from src.shared.models import (
    OHLCVCandle,
    TechnicalIndicators,
    SignalCreate,
    SignalType,
)


@pytest.fixture
def sample_candles():
    """Generate sample OHLCV candles for testing."""
    base_price = 50000
    candles = []

    for i in range(100):
        candles.append(
            OHLCVCandle(
                symbol="BTC/USDT",
                timeframe="15m",
                timestamp=datetime(2024, 1, 1, i // 4, (i % 4) * 15),
                open=Decimal(str(base_price + i * 10)),
                high=Decimal(str(base_price + i * 10 + 50)),
                low=Decimal(str(base_price + i * 10 - 50)),
                close=Decimal(str(base_price + i * 10 + 25)),
                volume=Decimal("100.5"),
            )
        )

    return candles


@pytest.fixture
def sample_prices():
    """Generate sample price list for indicator calculations."""
    return [50000 + i * 10 for i in range(100)]


@pytest.fixture
def sample_indicators():
    """Generate sample technical indicators."""
    return TechnicalIndicators(
        symbol="BTC/USDT",
        timestamp=datetime.utcnow(),
        rsi_14=35.5,
        sma_20=50500,
        sma_50=50000,
        macd_line=150.5,
        macd_signal=100.2,
        macd_histogram=50.3,
        bb_upper=51000,
        bb_middle=50500,
        bb_lower=50000,
        current_price=50250,
    )


@pytest.fixture
def sample_signal():
    """Generate sample signal for testing."""
    return SignalCreate(
        symbol="BTC/USDT",
        signal_type=SignalType.BUY,
        confidence=Decimal("92.5"),
        entry_price=Decimal("50000"),
        stop_loss_price=Decimal("49000"),
        take_profit_price=Decimal("52000"),
        analysis_summary="Strong bullish signals detected",
        technical_data={"rsi": 35.5, "macd": "bullish"},
    )


@pytest.fixture
def mock_db():
    """Mock database client."""
    mock = MagicMock()
    mock.get_candles.return_value = []
    mock.get_pending_signals.return_value = []
    mock.get_open_trades.return_value = []
    return mock


@pytest.fixture
def mock_exchange():
    """Mock CCXT exchange."""
    mock = AsyncMock()
    mock.fetch_ohlcv.return_value = [
        [1704067200000, 50000, 50100, 49900, 50050, 100.5] for _ in range(100)
    ]
    mock.fetch_balance.return_value = {
        "USDT": {"total": 10000, "free": 9000, "used": 1000}
    }
    mock.fetch_ticker.return_value = {"last": 50250}
    mock.create_order.return_value = {"id": "test-order-123", "average": 50000}
    return mock
