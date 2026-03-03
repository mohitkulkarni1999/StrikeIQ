"""
Async AI Database Layer for StrikeIQ
Replaces synchronous psycopg2 with asyncpg
"""

import asyncpg
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
from ..core.async_db import async_db

logger = logging.getLogger(__name__)

class AsyncAIDatabase:
    """Async AI-specific database operations"""
    
    def __init__(self):
        self._initialized = False
    
    async def initialize(self):
        """Initialize AI database"""
        if self._initialized:
            return
        
        # Ensure base database is initialized
        await async_db.initialize()
        self._initialized = True
        logger.info("✅ AI Database initialized")
    
    async def store_ai_signal(self, signal_data: Dict[str, Any]) -> bool:
        """Store AI signal in database"""
        try:
            query = """
                INSERT INTO ai_signals 
                (symbol, signal_type, confidence, timestamp, metadata)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (symbol, signal_type, timestamp) 
                DO UPDATE SET confidence = EXCLUDED.confidence, metadata = EXCLUDED.metadata
            """
            await async_db.execute(
                query,
                signal_data.get('symbol'),
                signal_data.get('signal_type'),
                signal_data.get('confidence'),
                signal_data.get('timestamp', datetime.utcnow()),
                signal_data.get('metadata', {})
            )
            return True
        except Exception as e:
            logger.error(f"Failed to store AI signal: {e}")
            return False
    
    async def get_recent_signals(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent AI signals for symbol"""
        try:
            query = """
                SELECT symbol, signal_type, confidence, timestamp, metadata
                FROM ai_signals 
                WHERE symbol = $1
                ORDER BY timestamp DESC
                LIMIT $2
            """
            return await async_db.fetch(query, symbol, limit)
        except Exception as e:
            logger.error(f"Failed to get recent signals: {e}")
            return []
    
    async def store_prediction(self, prediction_data: Dict[str, Any]) -> bool:
        """Store AI prediction"""
        try:
            query = """
                INSERT INTO ai_predictions 
                (symbol, prediction_type, predicted_value, confidence, 
                 target_timestamp, created_at, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """
            await async_db.execute(
                query,
                prediction_data.get('symbol'),
                prediction_data.get('prediction_type'),
                prediction_data.get('predicted_value'),
                prediction_data.get('confidence'),
                prediction_data.get('target_timestamp'),
                prediction_data.get('created_at', datetime.utcnow()),
                prediction_data.get('metadata', {})
            )
            return True
        except Exception as e:
            logger.error(f"Failed to store prediction: {e}")
            return False
    
    async def store_outcome(self, outcome_data: Dict[str, Any]) -> bool:
        """Store AI outcome for learning"""
        try:
            query = """
                INSERT INTO ai_outcomes 
                (symbol, prediction_id, actual_value, accuracy, 
                 outcome_timestamp, metadata)
                VALUES ($1, $2, $3, $4, $5, $6)
            """
            await async_db.execute(
                query,
                outcome_data.get('symbol'),
                outcome_data.get('prediction_id'),
                outcome_data.get('actual_value'),
                outcome_data.get('accuracy'),
                outcome_data.get('outcome_timestamp', datetime.utcnow()),
                outcome_data.get('metadata', {})
            )
            return True
        except Exception as e:
            logger.error(f"Failed to store outcome: {e}")
            return False
    
    async def store_market_snapshot(self, snapshot_data: Dict[str, Any]) -> bool:
        """Store market snapshot for AI training"""
        try:
            query = """
                INSERT INTO market_snapshots 
                (symbol, price_data, indicators, timestamp, metadata)
                VALUES ($1, $2, $3, $4, $5)
            """
            await async_db.execute(
                query,
                snapshot_data.get('symbol'),
                snapshot_data.get('price_data', {}),
                snapshot_data.get('indicators', {}),
                snapshot_data.get('timestamp', datetime.utcnow()),
                snapshot_data.get('metadata', {})
            )
            return True
        except Exception as e:
            logger.error(f"Failed to store market snapshot: {e}")
            return False
    
    async def get_training_data(self, symbol: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get training data for AI model"""
        try:
            query = """
                SELECT price_data, indicators, timestamp, metadata
                FROM market_snapshots 
                WHERE symbol = $1 
                AND timestamp >= NOW() - INTERVAL '%s days'
                ORDER BY timestamp ASC
            """ % days
            return await async_db.fetch(query, symbol)
        except Exception as e:
            logger.error(f"Failed to get training data: {e}")
            return []
    
    async def cleanup_old_data(self, days: int = 90) -> bool:
        """Clean up old data to prevent database bloat"""
        try:
            queries = [
                ("""
                    DELETE FROM market_snapshots 
                    WHERE timestamp < NOW() - INTERVAL '%s days'
                """ % days, ()),
                ("""
                    DELETE FROM ai_signals 
                    WHERE timestamp < NOW() - INTERVAL '%s days'
                """ % days, ())
            ]
            
            return await async_db.execute_transaction(queries)
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return False
    
    async def get_ai_metrics(self) -> Dict[str, Any]:
        """Get AI performance metrics"""
        try:
            # Get signal accuracy
            signal_accuracy = await async_db.fetchrow("""
                SELECT AVG(accuracy) as avg_accuracy, COUNT(*) as total_outcomes
                FROM ai_outcomes 
                WHERE outcome_timestamp >= NOW() - INTERVAL '7 days'
            """)
            
            # Get prediction counts
            prediction_counts = await async_db.fetchrow("""
                SELECT 
                    COUNT(*) as total_predictions,
                    COUNT(CASE WHEN confidence > 0.8 THEN 1 END) as high_confidence
                FROM ai_predictions 
                WHERE created_at >= NOW() - INTERVAL '7 days'
            """)
            
            return {
                "avg_accuracy": float(signal_accuracy.get('avg_accuracy', 0)) if signal_accuracy.get('avg_accuracy') else 0,
                "total_outcomes": int(signal_accuracy.get('total_outcomes', 0)),
                "total_predictions": int(prediction_counts.get('total_predictions', 0)),
                "high_confidence_predictions": int(prediction_counts.get('high_confidence', 0))
            }
        except Exception as e:
            logger.error(f"Failed to get AI metrics: {e}")
            return {}

# Global AI database instance
async_ai_db = AsyncAIDatabase()

# Convenience functions
async def get_ai_db():
    """Get AI database instance"""
    return async_ai_db

async def store_signal(signal_data: Dict[str, Any]) -> bool:
    """Store AI signal"""
    return await async_ai_db.store_ai_signal(signal_data)

async def store_prediction(prediction_data: Dict[str, Any]) -> bool:
    """Store AI prediction"""
    return await async_ai_db.store_prediction(prediction_data)

async def store_outcome(outcome_data: Dict[str, Any]) -> bool:
    """Store AI outcome"""
    return await async_ai_db.store_outcome(outcome_data)
