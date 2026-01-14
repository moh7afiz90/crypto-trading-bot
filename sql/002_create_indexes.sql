-- Market Data indexes
CREATE INDEX idx_market_data_symbol_timestamp ON market_data(symbol, timestamp DESC);
CREATE INDEX idx_market_data_symbol_timeframe_timestamp ON market_data(symbol, timeframe, timestamp DESC);

-- Sentiment Data indexes
CREATE INDEX idx_sentiment_data_source_timestamp ON sentiment_data(source, timestamp DESC);
CREATE INDEX idx_sentiment_data_symbol_timestamp ON sentiment_data(symbol, timestamp DESC) WHERE symbol IS NOT NULL;

-- Signals indexes
CREATE INDEX idx_signals_status ON signals(status);
CREATE INDEX idx_signals_symbol_status ON signals(symbol, status);
CREATE INDEX idx_signals_created_at ON signals(created_at DESC);
CREATE INDEX idx_signals_telegram_message_id ON signals(telegram_message_id) WHERE telegram_message_id IS NOT NULL;

-- Trades indexes
CREATE INDEX idx_trades_status ON trades(status);
CREATE INDEX idx_trades_signal_id ON trades(signal_id);
CREATE INDEX idx_trades_opened_at ON trades(opened_at DESC);

-- Portfolio indexes
CREATE INDEX idx_portfolio_timestamp ON portfolio(timestamp DESC);
