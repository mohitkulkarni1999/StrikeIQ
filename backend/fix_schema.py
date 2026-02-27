#!/usr/bin/env python3

from ai.ai_db import ai_db

def fix_formula_master_schema():
    """Fix formula_master table schema to match AI engine expectations"""
    
    try:
        ai_db.connect()
        print("Connected to database")
        
        # Add missing columns one by one
        statements = [
            'ALTER TABLE formula_master ADD COLUMN IF NOT EXISTS id TEXT',
            'ALTER TABLE formula_master ADD COLUMN IF NOT EXISTS formula_name TEXT', 
            'ALTER TABLE formula_master ADD COLUMN IF NOT EXISTS formula_type TEXT DEFAULT \'PCR_BASED\'',
            'ALTER TABLE formula_master ADD COLUMN IF NOT EXISTS conditions TEXT DEFAULT \'PCR > 1.2\'',
            'ALTER TABLE formula_master ADD COLUMN IF NOT EXISTS confidence_threshold FLOAT DEFAULT 0.5',
            'ALTER TABLE formula_master ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE'
        ]
        
        for statement in statements:
            try:
                ai_db.execute_query(statement)
                print(f'✓ {statement}')
            except Exception as e:
                print(f'✗ {statement}: {e}')
        
        # Update existing data
        update_statement = """
            UPDATE formula_master 
            SET 
                id = COALESCE(id, formula_id),
                formula_name = COALESCE(formula_name, name, 'Formula ' || formula_id),
                formula_type = COALESCE(formula_type, 'PCR_BASED'),
                conditions = COALESCE(conditions, 
                    CASE WHEN status = 'ACTIVE' THEN 'PCR > 1.2' ELSE 'HOLD' END
                ),
                confidence_threshold = COALESCE(confidence_threshold, 0.5),
                is_active = COALESCE(is_active, 
                    CASE WHEN status = 'ACTIVE' THEN TRUE ELSE FALSE END
                )
            WHERE formula_id IS NOT NULL
        """
        
        try:
            ai_db.execute_query(update_statement)
            print('✓ Updated existing data')
        except Exception as e:
            print(f'✗ Update failed: {e}')
        
        # Verify the fix
        result = ai_db.fetch_query('SELECT column_name FROM information_schema.columns WHERE table_name = \'formula_master\' ORDER BY ordinal_position')
        print('\nCurrent formula_master columns:')
        for row in result:
            print(f'  {row[0]}')
        
        ai_db.disconnect()
        print('\nSchema fix completed successfully')
        
    except Exception as e:
        print(f'Schema fix failed: {e}')
        if ai_db.connection:
            ai_db.disconnect()

if __name__ == "__main__":
    fix_formula_master_schema()
