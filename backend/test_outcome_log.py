#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai.ai_db import ai_db

def test_outcome_log():
    """Test the outcome_log table and the failing query"""
    
    print("=== Testing outcome_log table ===")
    
    # Connect to database
    if not ai_db.connect():
        print("❌ Failed to connect to database")
        return False
    
    # Check if table exists
    try:
        result = ai_db.fetch_query("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'outcome_log'
        """)
        
        if len(result) == 0:
            print("❌ outcome_log table does not exist")
            return False
        else:
            print("✅ outcome_log table exists")
    except Exception as e:
        print(f"❌ Error checking table existence: {e}")
        return False
    
    # Check table structure
    try:
        structure = ai_db.fetch_query("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'outcome_log' 
            ORDER BY ordinal_position
        """)
        
        print("📋 Table structure:")
        for col in structure:
            print(f"  {col[0]}: {col[1]} (nullable: {col[2]})")
    except Exception as e:
        print(f"❌ Error getting table structure: {e}")
        return False
    
    # Test the exact query that's failing
    try:
        print("\n=== Testing the failing query ===")
        query = """
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
        
        result = ai_db.fetch_one(query, params)
        
        if result:
            outcome_id = result[0]
            print(f"✅ Test query successful: outcome_id = {outcome_id}")
            
            # Clean up test record
            ai_db.execute_query("DELETE FROM outcome_log WHERE id = %s", (outcome_id,))
            print("🧹 Test record cleaned up")
            return True
        else:
            print("❌ Test query returned no result")
            return False
            
    except Exception as e:
        print(f"❌ Error testing insert query: {e}")
        return False
    
    finally:
        ai_db.disconnect()

if __name__ == "__main__":
    success = test_outcome_log()
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n💥 Tests failed!")
        sys.exit(1)
