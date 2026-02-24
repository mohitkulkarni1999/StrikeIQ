from datetime import datetime
from typing import Optional
import logging
from .ai_db import ai_db

logger = logging.getLogger(__name__)

class PredictionService:
    def __init__(self):
        self.db = ai_db
        
    def store_prediction(self, formula_id: str, signal: str, confidence: float, spot: float):
        """
        Store a prediction signal in the database
        
        Args:
            formula_id: Formula identifier (e.g., F01, F02, etc.)
            signal: Trading signal (BUY/SELL)
            confidence: Confidence level (0.0 to 1.0)
            spot: Current NIFTY spot price
        """
        try:
            query = """
                INSERT INTO prediction_log 
                (formula_id, signal, confidence, nifty_spot, prediction_time, outcome_checked)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            params = (
                formula_id,
                signal,
                confidence,
                spot,
                datetime.now(),
                False  # outcome_checked = False initially
            )
            
            success = self.db.execute_query(query, params)
            
            if success:
                logger.info(f"Prediction stored: {formula_id} {signal} @ {spot} (confidence: {confidence})")
                return True
            else:
                logger.error(f"Failed to store prediction for {formula_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error storing prediction: {e}")
            return False
            
    def get_pending_predictions(self):
        """Get all predictions that haven't been checked for outcomes"""
        try:
            query = """
                SELECT id, formula_id, signal, confidence, nifty_spot, prediction_time
                FROM prediction_log
                WHERE outcome_checked = FALSE
                AND prediction_time <= NOW() - INTERVAL '5 minutes'
                ORDER BY prediction_time ASC
            """
            
            results = self.db.fetch_query(query)
            
            pending_predictions = []
            for row in results:
                pending_predictions.append({
                    'id': row[0],
                    'formula_id': row[1],
                    'signal': row[2],
                    'confidence': row[3],
                    'nifty_spot': row[4],
                    'prediction_time': row[5]
                })
                
            logger.info(f"Found {len(pending_predictions)} pending predictions")
            return pending_predictions
            
        except Exception as e:
            logger.error(f"Error fetching pending predictions: {e}")
            return []
            
    def mark_prediction_checked(self, prediction_id: int, outcome: str):
        """Mark a prediction as checked and update its outcome"""
        try:
            query = """
                UPDATE prediction_log
                SET outcome = %s, outcome_checked = TRUE, outcome_time = %s
                WHERE id = %s
            """
            
            params = (outcome, datetime.now(), prediction_id)
            success = self.db.execute_query(query, params)
            
            if success:
                logger.info(f"Prediction {prediction_id} marked as checked with outcome: {outcome}")
                return True
            else:
                logger.error(f"Failed to mark prediction {prediction_id} as checked")
                return False
                
        except Exception as e:
            logger.error(f"Error marking prediction as checked: {e}")
            return False

# Global prediction service instance
prediction_service = PredictionService()
