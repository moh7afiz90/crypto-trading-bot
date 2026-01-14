# Crypto Trading Bot

AI-powered automated crypto trading system with Telegram notifications.

## Features

- **Data Collection**: Fetches OHLCV data from Binance, Fear & Greed Index, and CoinGecko sentiment
- **AI Analysis**: Uses GPT-4o-mini to analyze market conditions and generate signals
- **90% Confidence Threshold**: Only creates signals when AI confidence is >= 90%
- **Telegram Notifications**: Sends signals with Approve/Reject buttons
- **Automated Trading**: Executes approved trades on Binance testnet
- **Risk Management**: 2% risk per trade, 2% stop loss, 4% take profit

## Architecture

```
crypto-trading-bot/
├── src/
│   ├── shared/           # Shared modules (config, db, models, indicators)
│   ├── data_collector/   # Fetches market data (cron every 15 min)
│   ├── analysis_agent/   # AI signal generation (cron every 15 min)
│   ├── telegram_bot/     # Notifications & approvals (long-running)
│   └── trader/           # Trade execution (cron every 5 min)
├── sql/                  # Database schema for Supabase
└── tests/                # Unit tests
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required variables:
- `SUPABASE_URL` & `SUPABASE_KEY` - Supabase project credentials
- `BINANCE_API_KEY` & `BINANCE_SECRET` - Binance testnet API keys
- `OPENAI_API_KEY` - OpenAI API key
- `TELEGRAM_BOT_TOKEN` & `TELEGRAM_CHAT_ID` - Telegram bot credentials

### 3. Setup Database

Run the SQL files in order in your Supabase SQL editor:

1. `sql/001_create_tables.sql`
2. `sql/002_create_indexes.sql`
3. `sql/003_create_functions.sql`

### 4. Run Services Locally

```bash
# Data Collector
python -m src.data_collector.main

# Analysis Agent
python -m src.analysis_agent.main

# Telegram Bot
python -m src.telegram_bot.main

# Trader
python -m src.trader.main
```

## Deployment (Railway)

Create 4 Railway services:

| Service | Command | Schedule |
|---------|---------|----------|
| data-collector | `python -m src.data_collector.main` | `*/15 * * * *` |
| analysis-agent | `python -m src.analysis_agent.main` | `5,20,35,50 * * * *` |
| telegram-bot | `python -m src.telegram_bot.main` | (none - long-running) |
| trader | `python -m src.trader.main` | `*/5 * * * *` |

## Configuration

Key parameters in `src/shared/config.py`:

```python
MIN_CONFIDENCE = 90       # Only signal at 90%+ confidence
RISK_PER_TRADE = 0.02     # 2% risk per trade
STOP_LOSS_PCT = 0.02      # 2% stop loss
TAKE_PROFIT_PCT = 0.04    # 4% take profit
MAX_OPEN_POSITIONS = 5    # Max concurrent positions
```

## Testing

```bash
pytest tests/
```

## Important Notes

- Uses Binance TESTNET - no real money involved
- All trades require manual Telegram approval
- High confidence threshold (90%) means fewer but higher quality signals
