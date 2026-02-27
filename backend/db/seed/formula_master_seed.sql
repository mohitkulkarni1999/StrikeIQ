-- Formula Master Seed Data
-- Initial AI formulas for StrikeIQ trading system

-- Clear existing data
TRUNCATE TABLE formula_master RESTART IDENTITY CASCADE;

-- PCR-based formulas
INSERT INTO formula_master (id, formula_name, formula_type, conditions, confidence_threshold, is_active) VALUES
('F01', 'High PCR Bullish', 'PCR', 'PCR > 1.2 AND total_call_oi > 2000000', 0.6, TRUE),
('F02', 'Low PCR Bearish', 'PCR', 'PCR < 0.8 AND total_put_oi > 1500000', 0.6, TRUE),
('F03', 'Extreme PCR Reversal', 'PCR', 'PCR > 2.0 OR PCR < 0.5', 0.7, TRUE),

-- OI-based formulas
('F04', 'Call OI Dominance', 'OI', 'total_call_oi > total_put_oi * 1.5', 0.5, TRUE),
('F05', 'Put OI Dominance', 'OI', 'total_put_oi > total_call_oi * 1.5', 0.5, TRUE),
('F06', 'OI Balance Shift', 'OI', 'ABS(total_call_oi - total_put_oi) / (total_call_oi + total_put_oi) > 0.3', 0.6, TRUE),

-- Combined formulas
('F07', 'PCR + OI Bullish', 'COMBINED', 'PCR > 1.1 AND total_put_oi > total_call_oi * 1.2', 0.7, TRUE),
('F08', 'PCR + OI Bearish', 'COMBINED', 'PCR < 0.9 AND total_call_oi > total_put_oi * 1.2', 0.7, TRUE),

-- Volume-based formulas (placeholder for future implementation)
('F09', 'High Volume Signal', 'VOLUME', 'volume > 1000000', 0.5, FALSE),
('F10', 'Volume Spike', 'VOLUME', 'volume > AVG(volume) * 2', 0.6, FALSE);

-- Add indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_formula_master_active ON formula_master(is_active);
CREATE INDEX IF NOT EXISTS idx_formula_master_type ON formula_master(formula_type);
