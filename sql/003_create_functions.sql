-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_signals_updated_at
    BEFORE UPDATE ON signals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_trades_updated_at
    BEFORE UPDATE ON trades
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to get open positions count
CREATE OR REPLACE FUNCTION get_open_positions_count()
RETURNS INTEGER AS $$
BEGIN
    RETURN (SELECT COUNT(*) FROM trades WHERE status = 'OPEN');
END;
$$ LANGUAGE plpgsql;

-- Function to calculate total P&L
CREATE OR REPLACE FUNCTION calculate_total_pnl(start_date TIMESTAMPTZ DEFAULT NULL)
RETURNS DECIMAL AS $$
DECLARE
    total DECIMAL;
BEGIN
    SELECT COALESCE(SUM(pnl_amount), 0) INTO total
    FROM trades
    WHERE status IN ('CLOSED', 'STOPPED_OUT', 'TAKE_PROFIT')
    AND (start_date IS NULL OR closed_at >= start_date);
    RETURN total;
END;
$$ LANGUAGE plpgsql;

-- Function to expire old pending signals
CREATE OR REPLACE FUNCTION expire_old_signals()
RETURNS void AS $$
BEGIN
    UPDATE signals
    SET status = 'EXPIRED', updated_at = NOW()
    WHERE status = 'PENDING'
    AND expires_at < NOW();
END;
$$ LANGUAGE plpgsql;
