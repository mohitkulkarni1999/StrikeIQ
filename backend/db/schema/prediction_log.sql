-- Prediction Log Table Schema
-- Stores all AI predictions for tracking and evaluation

CREATE TABLE IF NOT EXISTS prediction_log (
    id SERIAL PRIMARY KEY,
    formula_id TEXT REFERENCES formula_master(id),
    signal TEXT NOT NULL, -- BUY, SELL, HOLD
    confidence FLOAT NOT NULL,
    nifty_spot FLOAT NOT NULL,
    prediction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    outcome_checked BOOLEAN DEFAULT FALSE,
    outcome TEXT, -- WIN, LOSS, HOLD
    outcome_time TIMESTAMP,
    strike_price FLOAT,
    option_type TEXT
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_prediction_log_formula_id ON prediction_log(formula_id);
CREATE INDEX IF NOT EXISTS idx_prediction_log_signal ON prediction_log(signal);
CREATE INDEX IF NOT EXISTS idx_prediction_log_prediction_time ON prediction_log(prediction_time);
CREATE INDEX IF NOT EXISTS idx_prediction_log_outcome_checked ON prediction_log(outcome_checked);
CREATE INDEX IF NOT EXISTS idx_prediction_log_outcome ON prediction_log(outcome);
