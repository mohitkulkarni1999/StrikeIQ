import os
import psycopg2
from ai.ai_db import ai_db

try:
    ai_db.connect()
    # Check if tables exist
    tables_to_check = ['formula_master', 'formula_experience', 'prediction_log', 'outcome_log']
    
    for table in tables_to_check:
        query = 'SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s)'
        result = ai_db.fetch_one(query, (table,))
        exists = result[0] if result else False
        print(f'Table {table}: {"EXISTS" if exists else "MISSING"}')
        
    ai_db.disconnect()
except Exception as e:
    print(f'Error: {e}')
