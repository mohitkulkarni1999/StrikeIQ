-- Market Snapshot Table Schema
-- Stores market data snapshots for AI analysis

CREATE TABLE IF NOT EXISTS market_snapshot (
    id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    spot_price FLOAT NOT NULL,
    pcr FLOAT, -- Put-Call Ratio
    total_call_oi FLOAT,
    total_put_oi FLOAT,
    atm_strike FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_market_snapshot_symbol ON market_snapshot(symbol);
CREATE INDEX IF NOT EXISTS idx_market_snapshot_timestamp ON market_snapshot(timestamp);
CREATE INDEX IF NOT EXISTS idx_market_snapshot_pcr ON market_snapshot(pcr);
CREATE INDEX IF NOT EXISTS idx_market_snapshot_atm ON market_snapshot(atm_strike);
