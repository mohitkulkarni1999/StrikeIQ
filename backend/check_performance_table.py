#!/usr/bin/env python3
"""
Check smart_money_predictions table structure
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy import create_engine, inspect
from app.core.config import settings

def check_performance_table():
    """Check performance table structure"""
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)
    
    # Check if table exists
    if 'smart_money_predictions' in inspector.get_table_names():
        # Get columns for smart_money_predictions
        columns = inspector.get_columns('smart_money_predictions')
        
        print("Current columns in smart_money_predictions:")
        for column in columns:
            print(f"  - {column['name']}: {column['type']}")
        
        # Get indexes
        indexes = inspector.get_indexes('smart_money_predictions')
        print("\nCurrent indexes:")
        for index in indexes:
            print(f"  - {index['name']}: {index['column_names']}")
    else:
        print("smart_money_predictions table does not exist")

if __name__ == "__main__":
    check_performance_table()
