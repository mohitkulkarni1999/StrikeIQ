#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai.ai_db import ai_db

def fix_outcome_log_schema():
    """Fix the outcome_log table schema to match AI outcome engine expectations"""
    
    print("=== Fixing outcome_log schema ===")
    
    # Connect to database
    if not ai_db.connect():
        print("❌ Failed to connect to database")
        return False
    
    try:
        # Drop the existing table
        print("🗑️ Dropping existing outcome_log table...")
        ai_db.execute_query("DROP TABLE IF EXISTS outcome_log")
        
        # Create table with correct schema
        print("🏗️ Creating outcome_log table with correct schema...")
        create_table_query = """
            CREATE TABLE outcome_log (
                id SERIAL PRIMARY KEY,
                prediction_id INTEGER REFERENCES prediction_log(id),
                formula_id TEXT,
                outcome TEXT NOT NULL,
                confidence FLOAT,
                evaluation_method TEXT,
                evaluation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                price_movement FLOAT,
                pnl FLOAT
            )
        """
        
        if not ai_db.execute_query(create_table_query):
            print("❌ Failed to create table")
            return False
        
        print("✅ Table created successfully")
        
        # Create indexes
        print("📊 Creating indexes...")
        indexes = [
            "CREATE INDEX idx_outcome_log_prediction_id ON outcome_log(prediction_id)",
            "CREATE INDEX idx_outcome_log_formula_id ON outcome_log(formula_id)",
            "CREATE INDEX idx_outcome_log_outcome ON outcome_log(outcome)",
            "CREATE INDEX idx_outcome_log_evaluation_time ON outcome_log(evaluation_time)",
            "CREATE INDEX idx_outcome_log_method ON outcome_log(evaluation_method)"
        ]
        
        for index_query in indexes:
            ai_db.execute_query(index_query)
        
        print("✅ Indexes created")
        
        # Test the fixed schema
        print("\n=== Testing fixed schema ===")
        test_query = """
            INSERT INTO outcome_log 
            (prediction_id, formula_id, outcome, confidence, evaluation_method, evaluation_time)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        
        params = (
            999,  # test prediction_id
            'test_formula',  # formula_id
            'HOLD',  # outcome
            0.5,  # confidence
            'TEST',  # evaluation_method
            '2026-03-03 12:00:00'  # evaluation_time
        )
        
        result = ai_db.fetch_one(test_query, params)
        
        if result:
            outcome_id = result[0]
            print(f"✅ Test query successful: outcome_id = {outcome_id}")
            
            # Clean up test record
            ai_db.execute_query("DELETE FROM outcome_log WHERE id = %s", (outcome_id,))
            print("🧹 Test record cleaned up")
            return True
        else:
            print("❌ Test query failed")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing schema: {e}")
        return False
    
    finally:
        ai_db.disconnect()

if __name__ == "__main__":
    success = fix_outcome_log_schema()
    if success:
        print("\n🎉 Schema fixed successfully!")
    else:
        print("\n💥 Schema fix failed!")
        sys.exit(1)
