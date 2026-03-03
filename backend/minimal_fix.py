import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai.ai_db import ai_db

def minimal_fix():
    print("=== Minimal Fix ===")
    
    # Connect
    ai_db.connect()
    
    try:
        # Drop table
        print("Dropping table...")
        ai_db.execute_query("DROP TABLE IF EXISTS outcome_log")
        
        # Create table with exact schema needed by AI outcome engine
        print("Creating table...")
        query = """
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
        ai_db.execute_query(query)
        print("✅ Table created")
        
        # Create just one essential index
        print("Creating index...")
        ai_db.execute_query("CREATE INDEX idx_outcome_log_prediction_id ON outcome_log(prediction_id)")
        print("✅ Index created")
        
        print("🎉 Fix completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        ai_db.disconnect()

if __name__ == "__main__":
    minimal_fix()
