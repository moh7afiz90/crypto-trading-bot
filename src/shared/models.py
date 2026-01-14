"""
Pydantic models and enums.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, Field


class SignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class SignalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"
    EXPIRED = "EXPIRED"


class TradeStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    STOPPED_OUT = "STOPPED_OUT"
    TAKE_PROFIT = "TAKE_PROFIT"


class SentimentSource(str, Enum):
    FEAR_GREED = "fear_greed"
    COINGECKO = "coingecko"


class OHLCVCandle(BaseModel):
    """OHLCV candle data."""
    symbol: str
    timeframe: str = "15m"
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }


class SentimentData(BaseModel):
    """Sentiment data from various sources."""
    source: SentimentSource
    symbol: Optional[str] = None
    timestamp: datetime
    value: Decimal = Field(ge=0, le=100)
    classification: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None


class TechnicalIndicators(BaseModel):
    """Calculated technical indicators."""
    symbol: str
    timestamp: datetime
    rsi_14: Optional[float] = None
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    macd_line: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    current_price: float


class SignalCreate(BaseModel):
    """Data to create a new signal."""
    symbol: str
    signal_type: SignalType
    confidence: Decimal = Field(ge=0, le=100)
    entry_price: Decimal
    stop_loss_price: Decimal
    take_profit_price: Decimal
    analysis_summary: Optional[str] = None
    technical_data: Optional[Dict[str, Any]] = None


class Signal(SignalCreate):
    """Full signal model."""
    id: UUID
    status: SignalStatus = SignalStatus.PENDING
    telegram_message_id: Optional[int] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class TradeCreate(BaseModel):
    """Data to create a new trade."""
    signal_id: Optional[UUID] = None
    symbol: str
    side: SignalType
    entry_price: Decimal
    quantity: Decimal
    stop_loss_price: Decimal
    take_profit_price: Decimal


class Trade(TradeCreate):
    """Full trade model."""
    id: UUID
    exit_price: Optional[Decimal] = None
    status: TradeStatus = TradeStatus.OPEN
    pnl_amount: Optional[Decimal] = None
    pnl_percentage: Optional[Decimal] = None
    exchange_order_id: Optional[str] = None
    sl_order_id: Optional[str] = None
    tp_order_id: Optional[str] = None
    opened_at: datetime
    closed_at: Optional[datetime] = None


class GPTAnalysisResponse(BaseModel):
    """Structured response from GPT analysis."""
    should_trade: bool
    signal_type: Optional[SignalType] = None
    confidence: float = Field(ge=0, le=100)
    reasoning: str
    key_factors: List[str]
    risk_assessment: str


class PortfolioBalance(BaseModel):
    """Portfolio balance."""
    asset: str = "USDT"
    total_balance: Decimal
    available_balance: Decimal
    locked_balance: Decimal = Decimal("0")
    timestamp: datetime
