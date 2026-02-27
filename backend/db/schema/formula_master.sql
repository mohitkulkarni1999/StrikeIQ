-- Formula Master Table Schema
-- Core AI formulas and trading strategies

CREATE TABLE IF NOT EXISTS formula_master (
    id TEXT PRIMARY KEY,
    formula_name TEXT NOT NULL,
    formula_type TEXT NOT NULL,
    conditions TEXT,
    confidence_threshold FLOAT DEFAULT 0.5,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_formula_master_active ON formula_master(is_active);
CREATE INDEX IF NOT EXISTS idx_formula_master_type ON formula_master(formula_type);
CREATE INDEX IF NOT EXISTS idx_formula_master_created ON formula_master(created_at);
