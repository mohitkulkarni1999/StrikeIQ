-- Paper Trade Log Table Schema
-- Tracks simulated trades for predictions

CREATE TABLE IF NOT EXISTS paper_trade_log (
    id SERIAL PRIMARY KEY,
    prediction_id INTEGER REFERENCES prediction_log(id),
    symbol TEXT NOT NULL,
    strike_price FLOAT NOT NULL,
    option_type TEXT NOT NULL, -- CE, PE
    entry_price FLOAT NOT NULL,
    exit_price FLOAT,
    quantity INTEGER DEFAULT 75,
    pnl FLOAT,
    trade_status TEXT DEFAULT 'OPEN', -- OPEN, CLOSED
    entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    exit_time TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_paper_trade_prediction_id ON paper_trade_log(prediction_id);
CREATE INDEX IF NOT EXISTS idx_paper_trade_symbol ON paper_trade_log(symbol);
CREATE INDEX IF NOT EXISTS idx_paper_trade_status ON paper_trade_log(trade_status);
CREATE INDEX IF NOT EXISTS idx_paper_trade_entry_time ON paper_trade_log(entry_time);
CREATE INDEX IF NOT EXISTS idx_paper_trade_option_type ON paper_trade_log(option_type);
