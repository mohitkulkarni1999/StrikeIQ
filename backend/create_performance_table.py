#!/usr/bin/env python3
"""
Create smart_money_predictions table for performance tracking
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy import create_engine, text
from app.core.config import settings

def create_performance_table():
    """Create smart_money_predictions table"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Create the table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS smart_money_predictions (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                symbol VARCHAR NOT NULL,
                bias VARCHAR NOT NULL,
                confidence FLOAT NOT NULL,
                pcr FLOAT,
                pcr_shift_z FLOAT,
                atm_straddle FLOAT,
                straddle_change_normalized FLOAT,
                oi_acceleration_ratio FLOAT,
                iv_regime VARCHAR,
                actual_move FLOAT,
                result VARCHAR,
                model_version VARCHAR DEFAULT 'v1.0',
                expiry_date VARCHAR
            )
        """))
        
        # Create indexes
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_smart_money_predictions_symbol 
            ON smart_money_predictions(symbol)
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_smart_money_predictions_timestamp 
            ON smart_money_predictions(timestamp)
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_smart_money_predictions_symbol_timestamp 
            ON smart_money_predictions(symbol, timestamp)
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_smart_money_predictions_result 
            ON smart_money_predictions(result)
        """))
        
        conn.commit()
        print("✅ Created smart_money_predictions table with indexes")

if __name__ == "__main__":
    create_performance_table()
