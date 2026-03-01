-- Outcome Log Table Schema
-- Detailed results of prediction evaluations

CREATE TABLE IF NOT EXISTS outcome_log (
    id SERIAL PRIMARY KEY,
    prediction_id INTEGER REFERENCES prediction_log(id),
    formula_id TEXT,
    outcome TEXT NOT NULL, -- WIN, LOSS, HOLD
    confidence FLOAT,
    evaluation_method TEXT, -- PAPER_TRADE_PNL, PRICE_MOVEMENT, ERROR
    evaluation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    price_movement FLOAT,
    pnl FLOAT
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_outcome_log_prediction_id ON outcome_log(prediction_id);
CREATE INDEX IF NOT EXISTS idx_outcome_log_formula_id ON outcome_log(formula_id);
CREATE INDEX IF NOT EXISTS idx_outcome_log_outcome ON outcome_log(outcome);
CREATE INDEX IF NOT EXISTS idx_outcome_log_evaluation_time ON outcome_log(evaluation_time);
CREATE INDEX IF NOT EXISTS idx_outcome_log_method ON outcome_log(evaluation_method);
