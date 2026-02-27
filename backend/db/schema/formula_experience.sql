-- Formula Experience Table Schema
-- Tracks learning and performance metrics for each formula

CREATE TABLE IF NOT EXISTS formula_experience (
    id SERIAL PRIMARY KEY,
    formula_id TEXT REFERENCES formula_master(id),
    total_tests INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    success_rate FLOAT DEFAULT 0.0,
    experience_adjusted_confidence FLOAT DEFAULT 0.5,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(formula_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_formula_experience_formula_id ON formula_experience(formula_id);
CREATE INDEX IF NOT EXISTS idx_formula_experience_success_rate ON formula_experience(success_rate);
CREATE INDEX IF NOT EXISTS idx_formula_experience_updated ON formula_experience(last_updated);
