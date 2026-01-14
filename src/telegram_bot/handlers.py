"""
Telegram command and callback handlers.
"""

from telegram import Update
from telegram.ext import ContextTypes

from src.shared.db import DatabaseClient
from src.shared.models import SignalStatus
from src.shared.logger import get_logger

logger = get_logger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    await update.message.reply_text(
        "<b>Crypto Trading Bot</b>\n\n"
        "Available commands:\n"
        "/status - Current bot status\n"
        "/portfolio - Portfolio balance\n"
        "/signals - Recent signals\n\n"
        "I'll send you trading signals for approval.",
        parse_mode="HTML",
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command."""
    try:
        open_trades = DatabaseClient.get_open_trades()
        pending_signals = DatabaseClient.get_pending_signals()
        portfolio = DatabaseClient.get_latest_portfolio()

        balance = f"${float(portfolio['total_balance']):,.2f}" if portfolio else "N/A"

        await update.message.reply_text(
            f"<b>Bot Status</b>\n\n"
            f"<b>Open Positions:</b> {len(open_trades)}\n"
            f"<b>Pending Signals:</b> {len(pending_signals)}\n"
            f"<b>Portfolio Balance:</b> {balance}\n",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Status command error: {e}")
        await update.message.reply_text("Error fetching status. Please try again.")


async def portfolio_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle /portfolio command."""
    try:
        portfolio = DatabaseClient.get_latest_portfolio()
        open_trades = DatabaseClient.get_open_trades()

        if not portfolio:
            await update.message.reply_text("No portfolio data available.")
            return

        message = (
            f"<b>Portfolio Overview</b>\n\n"
            f"<b>Total Balance:</b> ${float(portfolio['total_balance']):,.2f}\n"
            f"<b>Available:</b> ${float(portfolio['available_balance']):,.2f}\n"
            f"<b>In Positions:</b> ${float(portfolio['locked_balance']):,.2f}\n\n"
            f"<b>Open Positions:</b> {len(open_trades)}\n"
        )

        if open_trades:
            message += "\n<b>Active Trades:</b>\n"
            for trade in open_trades[:5]:
                message += (
                    f"- {trade['symbol']} {trade['side']} @ "
                    f"${float(trade['entry_price']):,.2f}\n"
                )

        await update.message.reply_text(message, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Portfolio command error: {e}")
        await update.message.reply_text("Error fetching portfolio. Please try again.")


async def signals_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /signals command."""
    try:
        pending = DatabaseClient.get_pending_signals()

        if not pending:
            await update.message.reply_text("No pending signals.")
            return

        message = f"<b>Pending Signals</b> ({len(pending)})\n\n"

        for signal in pending[:10]:
            emoji = "+" if signal["signal_type"] == "BUY" else "-"
            message += (
                f"{emoji} {signal['symbol']} - {signal['signal_type']}\n"
                f"   Entry: ${float(signal['entry_price']):,.2f} | "
                f"Confidence: {signal['confidence']}%\n\n"
            )

        await update.message.reply_text(message, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Signals command error: {e}")
        await update.message.reply_text("Error fetching signals. Please try again.")


async def handle_signal_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle approve/reject button callbacks."""
    query = update.callback_query
    await query.answer()

    try:
        parts = query.data.split("_")
        if len(parts) != 3:
            logger.error(f"Invalid callback data: {query.data}")
            return

        _, action, signal_id = parts
        username = update.effective_user.username or str(update.effective_user.id)

        if action == "approve":
            DatabaseClient.update_signal_status(
                signal_id=signal_id,
                status=SignalStatus.APPROVED,
                approved_by=username,
            )

            await query.edit_message_text(
                text=query.message.text + f"\n\n<b>APPROVED</b> by @{username}",
                parse_mode="HTML",
            )
            logger.info(f"Signal {signal_id} approved by {username}")

        elif action == "reject":
            DatabaseClient.update_signal_status(
                signal_id=signal_id,
                status=SignalStatus.REJECTED,
                approved_by=username,
            )

            await query.edit_message_text(
                text=query.message.text + f"\n\n<b>REJECTED</b> by @{username}",
                parse_mode="HTML",
            )
            logger.info(f"Signal {signal_id} rejected by {username}")

        else:
            logger.warning(f"Unknown callback action: {action}")

    except Exception as e:
        logger.error(f"Callback handling error: {e}", exc_info=True)
        await query.edit_message_text(
            text=query.message.text + "\n\nError processing action",
            parse_mode="HTML",
        )
