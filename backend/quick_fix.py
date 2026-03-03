#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai.ai_db import ai_db

def quick_fix():
    """Quick fix for outcome_log schema without hanging"""
    
    print("=== Quick Fix for outcome_log ===")
    
    # Connect to database
    if not ai_db.connect():
        print("❌ Failed to connect to database")
        return False
    
    try:
        # Drop existing table
        print("Dropping existing table...")
        ai_db.execute_query("DROP TABLE IF EXISTS outcome_log")
        
        # Create new table with minimal schema
        print("Creating new table...")
        create_query = """
            CREATE TABLE outcome_log (
                id SERIAL PRIMARY KEY,
                prediction_id INTEGER,
                formula_id TEXT,
                outcome TEXT NOT NULL,
                confidence FLOAT,
                evaluation_method TEXT,
                evaluation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        
        if ai_db.execute_query(create_query):
            print("✅ Table created successfully")
            
            # Create just one essential index
            ai_db.execute_query("CREATE INDEX idx_outcome_log_prediction_id ON outcome_log(prediction_id)")
            print("✅ Index created")
            
            return True
        else:
            print("❌ Failed to create table")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    finally:
        ai_db.disconnect()

if __name__ == "__main__":
    if quick_fix():
        print("🎉 Fix completed!")
    else:
        print("💥 Fix failed!")
