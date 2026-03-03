import psycopg2
import os

def create_outcome_log_table():
    # Database connection
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME', 'strikeiq'),
        user=os.getenv('DB_USER', 'strikeiq'),
        password=os.getenv('DB_PASSWORD', 'strikeiq123'),
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432')
    )
    cursor = conn.cursor()
    
    try:
        # Drop existing table
        cursor.execute("DROP TABLE IF EXISTS outcome_log")
        print("Table dropped")
        
        # Create new table
        create_query = """
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
        cursor.execute(create_query)
        print("Table created")
        
        # Create one index
        cursor.execute("CREATE INDEX idx_outcome_log_prediction_id ON outcome_log(prediction_id)")
        print("Index created")
        
        conn.commit()
        print("✅ Success!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    create_outcome_log_table()
