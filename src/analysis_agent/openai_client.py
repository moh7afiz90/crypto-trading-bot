"""
OpenAI GPT-4o-mini integration for trading signal analysis.
"""

from typing import Optional

from openai import AsyncOpenAI

from src.shared.config import API, TRADING
from src.shared.models import TechnicalIndicators, SignalType, GPTAnalysisResponse
from src.shared.logger import get_logger
from .analyzer import MarketContext

logger = get_logger(__name__)


SYSTEM_PROMPT = f"""You are an expert cryptocurrency trading analyst. Your task is to analyze market data and provide trading recommendations.

CRITICAL RULES:
1. Only recommend trades with {TRADING.MIN_CONFIDENCE}%+ confidence when multiple indicators align
2. Be conservative - missing a trade is better than a losing trade
3. Consider both technical and sentiment indicators
4. Account for current market conditions and volatility

TRADING PARAMETERS:
- Stop Loss: {TRADING.STOP_LOSS_PCT * 100}% from entry
- Take Profit: {TRADING.TAKE_PROFIT_PCT * 100}% from entry
- Risk per trade: {TRADING.RISK_PER_TRADE * 100}% of portfolio

You MUST respond with valid JSON in this exact format:
{{
    "should_trade": true/false,
    "signal_type": "BUY" or "SELL" or null,
    "confidence": 0-100,
    "reasoning": "detailed explanation",
    "key_factors": ["factor1", "factor2"],
    "risk_assessment": "risk level description"
}}"""


async def get_gpt_analysis(
    symbol: str,
    indicators: TechnicalIndicators,
    market_context: MarketContext,
) -> Optional[GPTAnalysisResponse]:
    """Get trading analysis from GPT-4o-mini."""
    client = AsyncOpenAI(api_key=API.OPENAI_API_KEY)

    user_prompt = f"""Analyze the following market data for {symbol}:

TECHNICAL INDICATORS:
- Current Price: ${indicators.current_price:,.2f}
- RSI (14): {indicators.rsi_14:.2f if indicators.rsi_14 else 'N/A'}
- SMA 20: ${indicators.sma_20:,.2f if indicators.sma_20 else 'N/A'}
- SMA 50: ${indicators.sma_50:,.2f if indicators.sma_50 else 'N/A'}
- MACD Line: {indicators.macd_line:.4f if indicators.macd_line else 'N/A'}
- MACD Signal: {indicators.macd_signal:.4f if indicators.macd_signal else 'N/A'}
- MACD Histogram: {indicators.macd_histogram:.4f if indicators.macd_histogram else 'N/A'}
- Bollinger Upper: ${indicators.bb_upper:,.2f if indicators.bb_upper else 'N/A'}
- Bollinger Middle: ${indicators.bb_middle:,.2f if indicators.bb_middle else 'N/A'}
- Bollinger Lower: ${indicators.bb_lower:,.2f if indicators.bb_lower else 'N/A'}

MARKET CONTEXT:
{market_context.summary}

ANALYSIS REQUEST:
Based on the above data, should I enter a trade? If yes, should it be BUY or SELL?
Only recommend a trade if you have {TRADING.MIN_CONFIDENCE}%+ confidence with multiple confirming indicators.
Respond with JSON only."""

    try:
        response = await client.chat.completions.create(
            model=API.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=1000,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content

        import json
        data = json.loads(content)

        # Convert signal_type string to enum if present
        signal_type = None
        if data.get("signal_type"):
            signal_type = SignalType(data["signal_type"].upper())

        analysis = GPTAnalysisResponse(
            should_trade=data.get("should_trade", False),
            signal_type=signal_type,
            confidence=data.get("confidence", 0),
            reasoning=data.get("reasoning", ""),
            key_factors=data.get("key_factors", []),
            risk_assessment=data.get("risk_assessment", ""),
        )

        logger.info(
            f"GPT analysis for {symbol}: "
            f"should_trade={analysis.should_trade}, "
            f"type={analysis.signal_type}, "
            f"confidence={analysis.confidence}%"
        )

        return analysis

    except Exception as e:
        logger.error(f"GPT analysis failed for {symbol}: {e}", exc_info=True)
        return None
