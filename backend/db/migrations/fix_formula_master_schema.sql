-- Fix formula_master table schema to match AI engine expectations
-- This migration adds missing columns and updates existing ones

-- Add missing columns if they don't exist
DO $$
BEGIN
    -- Check if column exists before adding
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='formula_master' AND column_name='id'
    ) THEN
        ALTER TABLE formula_master ADD COLUMN id TEXT;
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='formula_master' AND column_name='formula_name'
    ) THEN
        ALTER TABLE formula_master ADD COLUMN formula_name TEXT;
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='formula_master' AND column_name='formula_type'
    ) THEN
        ALTER TABLE formula_master ADD COLUMN formula_type TEXT;
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='formula_master' AND column_name='conditions'
    ) THEN
        ALTER TABLE formula_master ADD COLUMN conditions TEXT;
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='formula_master' AND column_name='confidence_threshold'
    ) THEN
        ALTER TABLE formula_master ADD COLUMN confidence_threshold FLOAT DEFAULT 0.5;
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='formula_master' AND column_name='is_active'
    ) THEN
        ALTER TABLE formula_master ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
    END IF;
END $$;

-- Update existing data to populate new columns
UPDATE formula_master 
SET 
    id = formula_id,
    formula_name = COALESCE(name, 'Formula ' || formula_id),
    formula_type = 'PCR_BASED',
    conditions = CASE 
        WHEN status = 'ACTIVE' THEN 'PCR > 1.2'
        ELSE 'HOLD'
    END,
    confidence_threshold = COALESCE(confidence_threshold, 0.5),
    is_active = CASE 
        WHEN status = 'ACTIVE' THEN TRUE
        ELSE FALSE
    END
WHERE id IS NULL;

-- Make id the primary key if it's not already
ALTER TABLE formula_master DROP CONSTRAINT IF EXISTS formula_master_pkey;
ALTER TABLE formula_master ADD PRIMARY KEY (id);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_formula_master_active ON formula_master(is_active);
CREATE INDEX IF NOT EXISTS idx_formula_master_type ON formula_master(formula_type);
CREATE INDEX IF NOT EXISTS idx_formula_master_created ON formula_master(created_at);
