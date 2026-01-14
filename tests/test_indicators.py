"""
Tests for technical indicator calculations.
"""

import pytest
from src.shared.indicators import (
    calculate_sma,
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_all_indicators,
)
from datetime import datetime


class TestSMA:
    def test_sma_basic(self, sample_prices):
        """Test basic SMA calculation."""
        sma = calculate_sma(sample_prices, 20)
        assert sma is not None
        assert isinstance(sma, float)

    def test_sma_insufficient_data(self):
        """Test SMA with insufficient data."""
        prices = [100, 200, 300]
        sma = calculate_sma(prices, 20)
        assert sma is None

    def test_sma_exact_period(self):
        """Test SMA with exactly period prices."""
        prices = [100] * 20
        sma = calculate_sma(prices, 20)
        assert sma == 100.0


class TestRSI:
    def test_rsi_basic(self, sample_prices):
        """Test basic RSI calculation."""
        rsi = calculate_rsi(sample_prices, 14)
        assert rsi is not None
        assert 0 <= rsi <= 100

    def test_rsi_insufficient_data(self):
        """Test RSI with insufficient data."""
        prices = [100, 200, 300]
        rsi = calculate_rsi(prices, 14)
        assert rsi is None

    def test_rsi_all_gains(self):
        """Test RSI with all upward movement."""
        prices = list(range(100, 200))
        rsi = calculate_rsi(prices, 14)
        assert rsi is not None
        assert rsi > 50


class TestMACD:
    def test_macd_basic(self, sample_prices):
        """Test basic MACD calculation."""
        macd_line, signal, histogram = calculate_macd(sample_prices)
        assert macd_line is not None
        assert signal is not None
        assert histogram is not None

    def test_macd_insufficient_data(self):
        """Test MACD with insufficient data."""
        prices = [100] * 10
        macd_line, signal, histogram = calculate_macd(prices)
        assert macd_line is None


class TestBollingerBands:
    def test_bb_basic(self, sample_prices):
        """Test basic Bollinger Bands calculation."""
        upper, middle, lower = calculate_bollinger_bands(sample_prices)
        assert upper is not None
        assert middle is not None
        assert lower is not None
        assert upper > middle > lower

    def test_bb_insufficient_data(self):
        """Test BB with insufficient data."""
        prices = [100] * 10
        upper, middle, lower = calculate_bollinger_bands(prices)
        assert upper is None


class TestAllIndicators:
    def test_calculate_all(self, sample_prices):
        """Test calculating all indicators at once."""
        indicators = calculate_all_indicators(
            "BTC/USDT", sample_prices, datetime.utcnow()
        )

        assert indicators.symbol == "BTC/USDT"
        assert indicators.rsi_14 is not None
        assert indicators.sma_20 is not None
        assert indicators.current_price == sample_prices[-1]
