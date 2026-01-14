"""
Position monitoring and management.
"""

from typing import Dict, Any

from src.shared.db import DatabaseClient
from src.shared.models import TradeStatus
from src.shared.logger import get_logger

logger = get_logger(__name__)


class PositionManager:
    """Monitors and manages open positions."""

    async def check_position(self, trade: Dict[str, Any], executor) -> None:
        """Check if a position has hit SL or TP."""
        symbol = trade["symbol"]
        entry_price = float(trade["entry_price"])
        stop_loss = float(trade["stop_loss_price"])
        take_profit = float(trade["take_profit_price"])
        side = trade["side"]
        quantity = float(trade["quantity"])

        # Get current price
        current_price = await executor.get_current_price(symbol)
        if current_price is None:
            logger.warning(f"Could not get price for {symbol}")
            return

        # Check stop loss / take profit
        if side == "BUY":
            hit_sl = current_price <= stop_loss
            hit_tp = current_price >= take_profit
        else:
            hit_sl = current_price >= stop_loss
            hit_tp = current_price <= take_profit

        if hit_sl or hit_tp:
            status = TradeStatus.STOPPED_OUT if hit_sl else TradeStatus.TAKE_PROFIT
            exit_price = stop_loss if hit_sl else take_profit

            # Calculate P&L
            if side == "BUY":
                pnl_amount = (exit_price - entry_price) * quantity
            else:
                pnl_amount = (entry_price - exit_price) * quantity

            pnl_percentage = (pnl_amount / (entry_price * quantity)) * 100

            # Close the position
            await executor.close_position(symbol, side, quantity)

            # Update database
            DatabaseClient.close_trade(
                trade_id=trade["id"],
                exit_price=exit_price,
                status=status,
                pnl_amount=pnl_amount,
                pnl_percentage=pnl_percentage,
            )

            logger.info(
                f"Position {symbol} closed: {status.value}, "
                f"P&L: ${pnl_amount:.2f} ({pnl_percentage:.2f}%)"
            )
