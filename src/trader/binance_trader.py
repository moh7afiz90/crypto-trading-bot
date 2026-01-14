"""
Binance trading client using CCXT.
"""

from typing import Optional, Dict, Any

import ccxt.async_support as ccxt

from src.shared.config import API
from src.shared.logger import get_logger

logger = get_logger(__name__)


class BinanceTrader:
    """CCXT Binance trading client."""

    def __init__(self):
        self.exchange: Optional[ccxt.binance] = None

    async def initialize(self) -> None:
        """Initialize the exchange connection."""
        self.exchange = ccxt.binance(
            {
                "apiKey": API.BINANCE_API_KEY,
                "secret": API.BINANCE_SECRET,
                "enableRateLimit": True,
                "options": {
                    "defaultType": "spot",
                },
            }
        )

        if API.BINANCE_TESTNET:
            self.exchange.set_sandbox_mode(True)
            logger.info("Using Binance TESTNET")

        await self.exchange.load_markets()
        logger.info("Exchange initialized")

    async def close(self) -> None:
        """Close exchange connection."""
        if self.exchange:
            await self.exchange.close()

    async def get_balance(self, asset: str = "USDT") -> float:
        """Get available balance for an asset."""
        if not self.exchange:
            raise RuntimeError("Exchange not initialized")

        balance = await self.exchange.fetch_balance()
        return float(balance.get(asset, {}).get("free", 0))

    async def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol."""
        if not self.exchange:
            return None

        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            return float(ticker["last"])
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            return None

    async def create_market_order(
        self, symbol: str, side: str, amount: float
    ) -> Optional[Dict[str, Any]]:
        """Create a market order."""
        if not self.exchange:
            return None

        try:
            order = await self.exchange.create_order(
                symbol=symbol,
                type="market",
                side=side.lower(),
                amount=amount,
            )
            logger.info(f"Market order executed: {order['id']}")
            return order
        except Exception as e:
            logger.error(f"Failed to create market order: {e}")
            return None

    async def create_stop_loss_order(
        self, symbol: str, side: str, amount: float, stop_price: float
    ) -> Optional[Dict[str, Any]]:
        """Create a stop loss order."""
        if not self.exchange:
            return None

        try:
            order = await self.exchange.create_order(
                symbol=symbol,
                type="stop_loss_limit",
                side=side.lower(),
                amount=amount,
                price=stop_price,
                params={"stopPrice": stop_price},
            )
            logger.info(f"Stop loss order placed: {order['id']}")
            return order
        except Exception as e:
            logger.error(f"Failed to create stop loss order: {e}")
            return None

    async def create_take_profit_order(
        self, symbol: str, side: str, amount: float, price: float
    ) -> Optional[Dict[str, Any]]:
        """Create a take profit order."""
        if not self.exchange:
            return None

        try:
            order = await self.exchange.create_order(
                symbol=symbol,
                type="take_profit_limit",
                side=side.lower(),
                amount=amount,
                price=price,
                params={"stopPrice": price},
            )
            logger.info(f"Take profit order placed: {order['id']}")
            return order
        except Exception as e:
            logger.error(f"Failed to create take profit order: {e}")
            return None

    def get_amount_precision(self, symbol: str, amount: float) -> str:
        """Round amount to exchange precision."""
        if not self.exchange:
            return str(amount)
        return self.exchange.amount_to_precision(symbol, amount)
