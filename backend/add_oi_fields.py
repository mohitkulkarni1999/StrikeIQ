#!/usr/bin/env python3
"""
Add prev_oi and oi_delta fields to option_chain_snapshots table
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy import create_engine, text
from app.core.config import settings

def add_oi_fields():
    """Add OI fields to option_chain_snapshots table"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Add prev_oi column
        try:
            conn.execute(text("ALTER TABLE option_chain_snapshots ADD COLUMN prev_oi INTEGER"))
            conn.commit()
            print("✅ Added prev_oi field")
        except Exception as e:
            print(f"prev_oi field issue: {e}")
            conn.rollback()
        
        # Add oi_delta column
        try:
            conn.execute(text("ALTER TABLE option_chain_snapshots ADD COLUMN oi_delta INTEGER"))
            conn.commit()
            print("✅ Added oi_delta field")
        except Exception as e:
            print(f"oi_delta field issue: {e}")
            conn.rollback()

if __name__ == "__main__":
    add_oi_fields()
