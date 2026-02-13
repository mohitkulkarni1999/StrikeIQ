#!/usr/bin/env python3
"""
Simple script to add missing fields to option_chain_snapshots table
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy import create_engine, text
from app.core.config import settings

def add_missing_fields():
    """Add missing fields to option_chain_snapshots table"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Add symbol column
        try:
            conn.execute(text("""
                ALTER TABLE option_chain_snapshots 
                ADD COLUMN symbol VARCHAR
            """))
            print("✅ Added symbol field")
        except Exception as e:
            print(f"Symbol field already exists: {e}")
        
        # Add prev_oi column
        try:
            conn.execute(text("""
                ALTER TABLE option_chain_snapshots 
                ADD COLUMN prev_oi INTEGER
            """))
            print("✅ Added prev_oi field")
        except Exception as e:
            print(f"prev_oi field already exists: {e}")
        
        # Add oi_delta column
        try:
            conn.execute(text("""
                ALTER TABLE option_chain_snapshots 
                ADD COLUMN oi_delta INTEGER
            """))
            print("✅ Added oi_delta field")
        except Exception as e:
            print(f"oi_delta field already exists: {e}")
        
        # Create indexes
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_option_chain_symbol 
                ON option_chain_snapshots(symbol)
            """))
            print("✅ Created symbol index")
        except Exception as e:
            print(f"Symbol index already exists: {e}")
        
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_option_chain_symbol_timestamp 
                ON option_chain_snapshots(symbol, timestamp)
            """))
            print("✅ Created symbol_timestamp index")
        except Exception as e:
            print(f"Symbol_timestamp index already exists: {e}")
        
        conn.commit()
        print("✅ All missing fields added successfully")

if __name__ == "__main__":
    add_missing_fields()
