"""
Telegram InlineKeyboard builders.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def create_signal_keyboard(signal_id: str) -> InlineKeyboardMarkup:
    """Create approve/reject keyboard for a signal."""
    keyboard = [
        [
            InlineKeyboardButton(
                "Approve", callback_data=f"signal_approve_{signal_id}"
            ),
            InlineKeyboardButton(
                "Reject", callback_data=f"signal_reject_{signal_id}"
            ),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
