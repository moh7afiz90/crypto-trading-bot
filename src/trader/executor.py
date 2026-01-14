"""
Trade execution logic.
"""

from decimal import Decimal
from typing import Optional, Dict, Any

from src.shared.config import TRADING
from src.shared.db import DatabaseClient
from src.shared.models import TradeCreate, SignalType
from src.shared.logger import get_logger
from .binance_trader import BinanceTrader

logger = get_logger(__name__)


class TradeExecutor:
    """Handles trade execution on Binance testnet."""

    def __init__(self):
        self.trader = BinanceTrader()

    async def initialize(self) -> None:
        """Initialize the trading client."""
        await self.trader.initialize()

    async def close(self) -> None:
        """Close connections."""
        await self.trader.close()

    async def execute_signal(self, signal: Dict[str, Any]) -> bool:
        """Execute a trading signal."""
        symbol = signal["symbol"]
        side = signal["signal_type"]
        entry_price = float(signal["entry_price"])
        stop_loss_price = float(signal["stop_loss_price"])
        take_profit_price = float(signal["take_profit_price"])

        try:
            # Get current balance
            usdt_balance = await self.trader.get_balance("USDT")

            # Calculate position size (2% risk)
            risk_amount = usdt_balance * TRADING.RISK_PER_TRADE

            # Calculate quantity based on stop loss distance
            sl_distance = abs(entry_price - stop_loss_price)
            if sl_distance == 0:
                logger.error("Invalid stop loss distance")
                return False

            quantity = risk_amount / sl_distance

            # Ensure we have enough balance
            position_value = quantity * entry_price
            if position_value > usdt_balance * 0.95:
                quantity = (usdt_balance * 0.95) / entry_price

            # Round to exchange precision
            quantity = float(self.trader.get_amount_precision(symbol, quantity))

            logger.info(
                f"Executing {side} {symbol}: "
                f"qty={quantity}, entry={entry_price}, "
                f"sl={stop_loss_price}, tp={take_profit_price}"
            )

            # 1. Place main order
            main_order = await self.trader.create_market_order(
                symbol=symbol, side=side.lower(), amount=quantity
            )

            if not main_order:
                logger.error("Failed to execute main order")
                return False

            actual_entry = float(main_order.get("average", entry_price))

            # 2. Place stop loss order
            sl_side = "sell" if side == "BUY" else "buy"
            sl_order = await self.trader.create_stop_loss_order(
                symbol=symbol,
                side=sl_side,
                amount=quantity,
                stop_price=stop_loss_price,
            )

            # 3. Place take profit order
            tp_order = await self.trader.create_take_profit_order(
                symbol=symbol,
                side=sl_side,
                amount=quantity,
                price=take_profit_price,
            )

            # Record trade in database
            trade = TradeCreate(
                signal_id=signal["id"],
                symbol=symbol,
                side=SignalType(side),
                entry_price=Decimal(str(actual_entry)),
                quantity=Decimal(str(quantity)),
                stop_loss_price=Decimal(str(stop_loss_price)),
                take_profit_price=Decimal(str(take_profit_price)),
            )

            created_trade = DatabaseClient.create_trade(trade)

            # Update with order IDs
            DatabaseClient.update_trade_order_ids(
                trade_id=str(created_trade.id),
                exchange_order_id=main_order.get("id"),
                sl_order_id=sl_order.get("id") if sl_order else None,
                tp_order_id=tp_order.get("id") if tp_order else None,
            )

            logger.info(f"Trade recorded: {created_trade.id}")
            return True

        except Exception as e:
            logger.error(f"Trade execution failed for {symbol}: {e}", exc_info=True)
            return False

    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol."""
        return await self.trader.get_current_price(symbol)

    async def close_position(
        self, symbol: str, side: str, quantity: float
    ) -> Optional[Dict[str, Any]]:
        """Close a position by market order."""
        close_side = "sell" if side == "BUY" else "buy"
        return await self.trader.create_market_order(
            symbol=symbol, side=close_side, amount=quantity
        )

    async def sync_portfolio(self) -> None:
        """Sync portfolio balance from exchange."""
        try:
            if not self.trader.exchange:
                return

            balance = await self.trader.exchange.fetch_balance()
            usdt = balance.get("USDT", {})

            DatabaseClient.update_portfolio(
                total_balance=float(usdt.get("total", 0)),
                available_balance=float(usdt.get("free", 0)),
                locked_balance=float(usdt.get("used", 0)),
            )

            logger.info(
                f"Portfolio synced: "
                f"total=${usdt.get('total', 0):.2f}, "
                f"available=${usdt.get('free', 0):.2f}"
            )
        except Exception as e:
            logger.error(f"Portfolio sync failed: {e}")
