"""
Trader Service Entry Point.
Runs as a Railway cron job every 5 minutes.
"""

import asyncio
from datetime import datetime

from src.shared.config import validate_config, TRADING
from src.shared.db import DatabaseClient
from src.shared.models import SignalStatus
from src.shared.logger import get_logger
from .executor import TradeExecutor
from .position_manager import PositionManager

logger = get_logger(__name__)


async def execute_trading_cycle() -> None:
    """Main trading cycle orchestrator."""
    logger.info("Starting trading cycle")
    start_time = datetime.utcnow()

    executor = TradeExecutor()
    position_manager = PositionManager()

    try:
        await executor.initialize()

        # 1. Check and execute approved signals
        approved_signals = DatabaseClient.get_approved_signals()
        open_positions = DatabaseClient.get_open_trades_count()

        logger.info(
            f"Found {len(approved_signals)} approved signals, "
            f"{open_positions} open positions"
        )

        for signal in approved_signals:
            # Check position limit
            if open_positions >= TRADING.MAX_OPEN_POSITIONS:
                logger.warning(
                    f"Max positions ({TRADING.MAX_OPEN_POSITIONS}) reached, "
                    f"skipping signal {signal['id']}"
                )
                continue

            # Execute the trade
            success = await executor.execute_signal(signal)

            if success:
                open_positions += 1
                DatabaseClient.update_signal_status(
                    signal_id=signal["id"], status=SignalStatus.EXECUTED
                )

        # 2. Monitor open positions for SL/TP
        open_trades = DatabaseClient.get_open_trades()

        for trade in open_trades:
            await position_manager.check_position(trade, executor)

        # 3. Update portfolio balance
        await executor.sync_portfolio()

        elapsed = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Trading cycle completed in {elapsed:.2f}s")

    except Exception as e:
        logger.error(f"Trading cycle failed: {e}", exc_info=True)
        raise

    finally:
        await executor.close()


def main() -> None:
    """Entry point for Railway cron job."""
    validate_config()
    asyncio.run(execute_trading_cycle())


if __name__ == "__main__":
    main()
