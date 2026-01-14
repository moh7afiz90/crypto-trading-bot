"""
Supabase database client.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from supabase import create_client, Client

from .config import API
from .models import (
    OHLCVCandle,
    SentimentData,
    Signal,
    SignalCreate,
    SignalStatus,
    Trade,
    TradeCreate,
    TradeStatus,
)
from .logger import get_logger

logger = get_logger(__name__)


class DatabaseClient:
    """Supabase client wrapper."""

    _instance: Optional[Client] = None

    @classmethod
    def get_client(cls) -> Client:
        """Get or create Supabase client."""
        if cls._instance is None:
            cls._instance = create_client(API.SUPABASE_URL, API.SUPABASE_KEY)
        return cls._instance

    # ==================== Market Data ====================

    @classmethod
    def insert_candles(cls, candles: List[OHLCVCandle]) -> None:
        """Insert OHLCV candles with upsert."""
        client = cls.get_client()
        data = [
            {
                "symbol": c.symbol,
                "timeframe": c.timeframe,
                "timestamp": c.timestamp.isoformat(),
                "open": float(c.open),
                "high": float(c.high),
                "low": float(c.low),
                "close": float(c.close),
                "volume": float(c.volume),
            }
            for c in candles
        ]
        client.table("market_data").upsert(
            data, on_conflict="symbol,timeframe,timestamp"
        ).execute()
        logger.info(f"Inserted {len(candles)} candles")

    @classmethod
    def get_candles(
        cls, symbol: str, timeframe: str = "15m", limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get recent candles for a symbol."""
        client = cls.get_client()
        response = (
            client.table("market_data")
            .select("*")
            .eq("symbol", symbol)
            .eq("timeframe", timeframe)
            .order("timestamp", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data

    # ==================== Sentiment Data ====================

    @classmethod
    def insert_sentiment(cls, sentiment: SentimentData) -> None:
        """Insert sentiment data."""
        client = cls.get_client()
        data = {
            "source": sentiment.source.value,
            "symbol": sentiment.symbol,
            "timestamp": sentiment.timestamp.isoformat(),
            "value": float(sentiment.value),
            "classification": sentiment.classification,
            "raw_data": sentiment.raw_data,
        }
        client.table("sentiment_data").upsert(
            data, on_conflict="source,symbol,timestamp"
        ).execute()
        logger.info(f"Inserted sentiment from {sentiment.source}")

    @classmethod
    def get_latest_sentiment(
        cls, source: str, symbol: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get most recent sentiment data."""
        client = cls.get_client()
        query = client.table("sentiment_data").select("*").eq("source", source)

        if symbol:
            query = query.eq("symbol", symbol)
        else:
            query = query.is_("symbol", "null")

        response = query.order("timestamp", desc=True).limit(1).execute()
        return response.data[0] if response.data else None

    # ==================== Signals ====================

    @classmethod
    def create_signal(cls, signal: SignalCreate, expiry_hours: int = 4) -> Signal:
        """Create a new trading signal."""
        client = cls.get_client()
        data = {
            "symbol": signal.symbol,
            "signal_type": signal.signal_type.value,
            "confidence": float(signal.confidence),
            "entry_price": float(signal.entry_price),
            "stop_loss_price": float(signal.stop_loss_price),
            "take_profit_price": float(signal.take_profit_price),
            "analysis_summary": signal.analysis_summary,
            "technical_data": signal.technical_data,
            "expires_at": (datetime.utcnow() + timedelta(hours=expiry_hours)).isoformat(),
        }

        response = client.table("signals").insert(data).execute()
        logger.info(f"Created signal: {signal.signal_type} {signal.symbol}")
        return Signal(**response.data[0])

    @classmethod
    def get_pending_signals(cls) -> List[Dict[str, Any]]:
        """Get all pending signals that haven't expired."""
        client = cls.get_client()
        response = (
            client.table("signals")
            .select("*")
            .eq("status", SignalStatus.PENDING.value)
            .gt("expires_at", datetime.utcnow().isoformat())
            .order("created_at", desc=True)
            .execute()
        )
        return response.data

    @classmethod
    def update_signal_status(
        cls,
        signal_id: str,
        status: SignalStatus,
        telegram_message_id: Optional[int] = None,
        approved_by: Optional[str] = None,
    ) -> None:
        """Update signal status."""
        client = cls.get_client()
        data = {"status": status.value}

        if telegram_message_id:
            data["telegram_message_id"] = telegram_message_id
        if approved_by:
            data["approved_by"] = approved_by
            data["approved_at"] = datetime.utcnow().isoformat()

        client.table("signals").update(data).eq("id", signal_id).execute()
        logger.info(f"Updated signal {signal_id} to {status.value}")

    @classmethod
    def get_signal_by_message_id(cls, message_id: int) -> Optional[Dict[str, Any]]:
        """Get signal by Telegram message ID."""
        client = cls.get_client()
        response = (
            client.table("signals")
            .select("*")
            .eq("telegram_message_id", message_id)
            .execute()
        )
        return response.data[0] if response.data else None

    @classmethod
    def get_approved_signals(cls) -> List[Dict[str, Any]]:
        """Get approved signals ready for execution."""
        client = cls.get_client()
        response = (
            client.table("signals")
            .select("*")
            .eq("status", SignalStatus.APPROVED.value)
            .execute()
        )
        return response.data

    @classmethod
    def get_signal_by_id(cls, signal_id: str) -> Optional[Dict[str, Any]]:
        """Get signal by ID."""
        client = cls.get_client()
        response = client.table("signals").select("*").eq("id", signal_id).execute()
        return response.data[0] if response.data else None

    # ==================== Trades ====================

    @classmethod
    def create_trade(cls, trade: TradeCreate) -> Trade:
        """Create a new trade record."""
        client = cls.get_client()
        data = {
            "signal_id": str(trade.signal_id) if trade.signal_id else None,
            "symbol": trade.symbol,
            "side": trade.side.value,
            "entry_price": float(trade.entry_price),
            "quantity": float(trade.quantity),
            "stop_loss_price": float(trade.stop_loss_price),
            "take_profit_price": float(trade.take_profit_price),
        }
        response = client.table("trades").insert(data).execute()
        logger.info(f"Created trade: {trade.side} {trade.symbol}")
        return Trade(**response.data[0])

    @classmethod
    def get_open_trades(cls) -> List[Dict[str, Any]]:
        """Get all open trades."""
        client = cls.get_client()
        response = (
            client.table("trades")
            .select("*")
            .eq("status", TradeStatus.OPEN.value)
            .execute()
        )
        return response.data

    @classmethod
    def get_open_trades_count(cls) -> int:
        """Get count of open trades."""
        client = cls.get_client()
        response = (
            client.table("trades")
            .select("id", count="exact")
            .eq("status", TradeStatus.OPEN.value)
            .execute()
        )
        return response.count or 0

    @classmethod
    def close_trade(
        cls,
        trade_id: str,
        exit_price: float,
        status: TradeStatus,
        pnl_amount: float,
        pnl_percentage: float,
    ) -> None:
        """Close a trade with P&L."""
        client = cls.get_client()
        client.table("trades").update(
            {
                "exit_price": exit_price,
                "status": status.value,
                "pnl_amount": pnl_amount,
                "pnl_percentage": pnl_percentage,
                "closed_at": datetime.utcnow().isoformat(),
            }
        ).eq("id", trade_id).execute()
        logger.info(f"Closed trade {trade_id}: {status.value} P&L: {pnl_percentage:.2f}%")

    @classmethod
    def update_trade_order_ids(
        cls,
        trade_id: str,
        exchange_order_id: Optional[str] = None,
        sl_order_id: Optional[str] = None,
        tp_order_id: Optional[str] = None,
    ) -> None:
        """Update trade with exchange order IDs."""
        client = cls.get_client()
        data = {}
        if exchange_order_id:
            data["exchange_order_id"] = exchange_order_id
        if sl_order_id:
            data["sl_order_id"] = sl_order_id
        if tp_order_id:
            data["tp_order_id"] = tp_order_id

        if data:
            client.table("trades").update(data).eq("id", trade_id).execute()

    # ==================== Portfolio ====================

    @classmethod
    def update_portfolio(
        cls,
        total_balance: float,
        available_balance: float,
        locked_balance: float = 0,
    ) -> None:
        """Insert new portfolio snapshot."""
        client = cls.get_client()
        client.table("portfolio").insert(
            {
                "total_balance": total_balance,
                "available_balance": available_balance,
                "locked_balance": locked_balance,
                "timestamp": datetime.utcnow().isoformat(),
            }
        ).execute()

    @classmethod
    def get_latest_portfolio(cls) -> Optional[Dict[str, Any]]:
        """Get most recent portfolio balance."""
        client = cls.get_client()
        response = (
            client.table("portfolio")
            .select("*")
            .order("timestamp", desc=True)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None
