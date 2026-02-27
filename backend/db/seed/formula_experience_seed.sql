-- Formula Experience Seed Data
-- Initialize experience tracking for all formulas

-- Clear existing data
TRUNCATE TABLE formula_experience RESTART IDENTITY CASCADE;

-- Initialize experience for all formulas with default values
INSERT INTO formula_experience (formula_id, total_tests, wins, losses, success_rate, experience_adjusted_confidence) 
SELECT 
    id,
    0 as total_tests,
    0 as wins,
    0 as losses,
    0.0 as success_rate,
    confidence_threshold as experience_adjusted_confidence
FROM formula_master;

-- Add indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_formula_experience_formula_id ON formula_experience(formula_id);
CREATE INDEX IF NOT EXISTS idx_formula_experience_success_rate ON formula_experience(success_rate);
