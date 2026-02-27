"""
Create missing AI tables for StrikeIQ production-ready AI analytics engine
"""
import os
import psycopg2
from ai.ai_db import ai_db
import logging

logger = logging.getLogger(__name__)

def create_missing_tables():
    """Create missing AI tables if they don't exist"""
    
    try:
        ai_db.connect()
        logger.info("Connected to database, creating missing tables...")
        
        # Paper Trading table
        paper_trade_sql = """
        CREATE TABLE IF NOT EXISTS paper_trade_log (
            id SERIAL PRIMARY KEY,
            prediction_id INT,
            symbol TEXT,
            strike_price FLOAT,
            option_type TEXT,
            entry_price FLOAT,
            exit_price FLOAT,
            quantity INT,
            pnl FLOAT,
            trade_status TEXT,
            entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            exit_time TIMESTAMP
        );
        """
        
        # Market snapshot table for AI
        market_snapshot_sql = """
        CREATE TABLE IF NOT EXISTS market_snapshot (
            id SERIAL PRIMARY KEY,
            symbol TEXT,
            spot_price FLOAT,
            pcr FLOAT,
            total_call_oi FLOAT,
            total_put_oi FLOAT,
            atm_strike FLOAT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # AI event log
        ai_event_log_sql = """
        CREATE TABLE IF NOT EXISTS ai_event_log (
            id SERIAL PRIMARY KEY,
            event_type TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Create tables
        tables = [
            ("paper_trade_log", paper_trade_sql),
            ("market_snapshot", market_snapshot_sql), 
            ("ai_event_log", ai_event_log_sql)
        ]
        
        for table_name, sql in tables:
            try:
                ai_db.execute_query(sql)
                logger.info(f"Table {table_name} created successfully")
            except Exception as e:
                logger.error(f"Error creating table {table_name}: {e}")
                
        # Add indexes for performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_paper_trade_prediction_id ON paper_trade_log(prediction_id);",
            "CREATE INDEX IF NOT EXISTS idx_paper_trade_status ON paper_trade_log(trade_status);",
            "CREATE INDEX IF NOT EXISTS idx_market_snapshot_symbol ON market_snapshot(symbol);",
            "CREATE INDEX IF NOT EXISTS idx_market_snapshot_timestamp ON market_snapshot(timestamp);",
            "CREATE INDEX IF NOT EXISTS idx_ai_event_type ON ai_event_log(event_type);",
            "CREATE INDEX IF NOT EXISTS idx_ai_event_created_at ON ai_event_log(created_at);"
        ]
        
        for index_sql in indexes:
            try:
                ai_db.execute_query(index_sql)
                logger.info(f"Index created: {index_sql[:50]}...")
            except Exception as e:
                logger.warning(f"Index creation warning: {e}")
        
        logger.info("All missing AI tables created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error creating AI tables: {e}")
        return False
    finally:
        ai_db.disconnect()

if __name__ == "__main__":
    create_missing_tables()
