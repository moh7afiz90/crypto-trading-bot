"""
Telegram Bot Service Entry Point.
Runs as a long-running process.
"""

import asyncio
from typing import Optional

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
)

from src.shared.config import validate_config, API
from src.shared.db import DatabaseClient
from src.shared.models import SignalStatus
from src.shared.logger import get_logger
from .handlers import (
    start_command,
    status_command,
    portfolio_command,
    signals_command,
    handle_signal_callback,
)
from .keyboards import create_signal_keyboard

logger = get_logger(__name__)


class TelegramBotService:
    """Telegram bot service for signal notifications and approvals."""

    def __init__(self):
        self.application: Optional[Application] = None
        self.check_interval = 60

    async def send_signal_notification(self, signal: dict) -> None:
        """Send a signal notification with approve/reject buttons."""
        if not self.application:
            logger.error("Application not initialized")
            return

        message = self._format_signal_message(signal)
        keyboard = create_signal_keyboard(signal["id"])

        try:
            sent_message = await self.application.bot.send_message(
                chat_id=API.TELEGRAM_CHAT_ID,
                text=message,
                reply_markup=keyboard,
                parse_mode="HTML",
            )

            DatabaseClient.update_signal_status(
                signal_id=signal["id"],
                status=SignalStatus.PENDING,
                telegram_message_id=sent_message.message_id,
            )

            logger.info(f"Sent signal notification: {signal['id']}")

        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

    def _format_signal_message(self, signal: dict) -> str:
        """Format signal data as Telegram message."""
        signal_type = signal["signal_type"]
        technical = signal.get("technical_data", {}) or {}

        return f"""
<b>NEW TRADING SIGNAL</b>

<b>Symbol:</b> {signal['symbol']}
<b>Type:</b> {signal_type}
<b>Confidence:</b> {signal['confidence']}%

<b>Entry Price:</b> ${float(signal['entry_price']):,.2f}
<b>Stop Loss:</b> ${float(signal['stop_loss_price']):,.2f}
<b>Take Profit:</b> ${float(signal['take_profit_price']):,.2f}

<b>Technical Indicators:</b>
RSI: {technical.get('rsi', 'N/A')}
MACD: {technical.get('macd', 'N/A')}
BB Position: {technical.get('bb_position', 'N/A')}

<b>Analysis:</b>
{signal.get('analysis_summary', 'No analysis available')}

<i>Expires: {signal.get('expires_at', 'N/A')}</i>
"""

    async def check_pending_signals(self) -> None:
        """Periodically check for new pending signals to notify."""
        while True:
            try:
                pending_signals = DatabaseClient.get_pending_signals()

                for signal in pending_signals:
                    if not signal.get("telegram_message_id"):
                        await self.send_signal_notification(signal)

            except Exception as e:
                logger.error(f"Error checking pending signals: {e}")

            await asyncio.sleep(self.check_interval)

    async def run(self) -> None:
        """Start the Telegram bot."""
        logger.info("Starting Telegram bot...")

        self.application = Application.builder().token(API.TELEGRAM_BOT_TOKEN).build()

        self.application.add_handler(CommandHandler("start", start_command))
        self.application.add_handler(CommandHandler("status", status_command))
        self.application.add_handler(CommandHandler("portfolio", portfolio_command))
        self.application.add_handler(CommandHandler("signals", signals_command))
        self.application.add_handler(
            CallbackQueryHandler(handle_signal_callback, pattern="^signal_")
        )

        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()

        logger.info("Telegram bot started successfully")

        await self.check_pending_signals()


def main() -> None:
    """Entry point for Railway deployment."""
    validate_config()
    bot = TelegramBotService()
    asyncio.run(bot.run())


if __name__ == "__main__":
    main()
