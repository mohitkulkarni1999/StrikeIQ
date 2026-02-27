"""
AI Learning Engine for StrikeIQ

Responsibilities:
- Update formula_experience table based on outcomes
- Calculate success rates and experience-adjusted confidence
- Implement learning feedback loop
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from ai.ai_db import ai_db

logger = logging.getLogger(__name__)

class AILearningEngine:
    def __init__(self):
        self.db = ai_db
        self.learning_window_days = 30  # Learning window for experience calculation
        self.min_predictions_for_learning = 5  # Minimum predictions before learning kicks in
        
    def get_formula_performance(self, formula_id: str, days: int = 30) -> Dict:
        """
        Get performance statistics for a specific formula
        
        Returns:
            Dictionary with performance metrics
        """
        try:
            query = """
                SELECT 
                    COUNT(*) as total_predictions,
                    SUM(CASE WHEN o.outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN o.outcome = 'LOSS' THEN 1 ELSE 0 END) as losses,
                    SUM(CASE WHEN o.outcome = 'HOLD' THEN 1 ELSE 0 END) as holds,
                    AVG(o.confidence) as avg_confidence,
                    MAX(o.evaluation_time) as last_evaluation
                FROM prediction_log p
                LEFT JOIN outcome_log o ON p.id = o.prediction_id
                WHERE p.formula_id = %s
                AND p.prediction_time >= NOW() - INTERVAL %s
                AND p.signal IN ('BUY', 'SELL')
            """
            
            params = (formula_id, f"{days} days")
            result = self.db.fetch_one(query, params)
            
            if result:
                total_predictions = result[0] or 0
                wins = result[1] or 0
                losses = result[2] or 0
                holds = result[3] or 0
                avg_confidence = result[4] or 0.0
                last_evaluation = result[5]
                
                # Calculate success rate (excluding holds)
                considered_predictions = wins + losses
                success_rate = (wins / considered_predictions * 100) if considered_predictions > 0 else 0.0
                
                return {
                    'formula_id': formula_id,
                    'total_predictions': total_predictions,
                    'wins': wins,
                    'losses': losses,
                    'holds': holds,
                    'success_rate': round(success_rate, 2),
                    'avg_confidence': round(avg_confidence, 2),
                    'last_evaluation': last_evaluation,
                    'period_days': days
                }
            else:
                return {
                    'formula_id': formula_id,
                    'total_predictions': 0,
                    'wins': 0,
                    'losses': 0,
                    'holds': 0,
                    'success_rate': 0.0,
                    'avg_confidence': 0.0,
                    'last_evaluation': None,
                    'period_days': days
                }
                
        except Exception as e:
            logger.error(f"Error getting formula performance for {formula_id}: {e}")
            return {
                'formula_id': formula_id,
                'total_predictions': 0,
                'wins': 0,
                'losses': 0,
                'holds': 0,
                'success_rate': 0.0,
                'avg_confidence': 0.0,
                'last_evaluation': None,
                'period_days': days
            }
    
    def get_current_formula_experience(self, formula_id: str) -> Optional[Dict]:
        """Get current formula experience from database"""
        try:
            query = """
                SELECT total_tests, wins, losses, success_rate, experience_adjusted_confidence, last_updated
                FROM formula_experience
                WHERE formula_id = %s
            """
            
            result = self.db.fetch_one(query, (formula_id,))
            
            if result:
                return {
                    'formula_id': formula_id,
                    'total_tests': result[0] or 0,
                    'wins': result[1] or 0,
                    'losses': result[2] or 0,
                    'success_rate': result[3] or 0.0,
                    'experience_adjusted_confidence': result[4] or 0.0,
                    'last_updated': result[5]
                }
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting current formula experience for {formula_id}: {e}")
            return None
    
    def calculate_experience_adjusted_confidence(self, base_confidence: float, success_rate: float, total_tests: int) -> float:
        """
        Calculate experience-adjusted confidence based on historical performance
        
        Args:
            base_confidence: Original confidence from formula
            success_rate: Historical success rate (percentage)
            total_tests: Number of predictions made
            
        Returns:
            Adjusted confidence value
        """
        try:
            # Weight factors
            experience_weight = min(0.4, total_tests / 100.0)  # Max 40% weight for experience
            base_weight = 1.0 - experience_weight
            
            # Adjust confidence based on success rate
            if success_rate >= 60:  # Good performance
                performance_multiplier = 1.2
            elif success_rate >= 50:  # Average performance
                performance_multiplier = 1.0
            elif success_rate >= 40:  # Below average
                performance_multiplier = 0.8
            else:  # Poor performance
                performance_multiplier = 0.6
            
            # Calculate adjusted confidence
            adjusted_confidence = (base_confidence * base_weight * performance_multiplier + 
                                 success_rate / 100.0 * experience_weight)
            
            # Ensure confidence stays within valid range
            adjusted_confidence = max(0.1, min(0.95, adjusted_confidence))
            
            return round(adjusted_confidence, 3)
            
        except Exception as e:
            logger.error(f"Error calculating experience-adjusted confidence: {e}")
            return base_confidence
    
    def update_formula_experience(self, formula_id: str) -> bool:
        """
        Update formula experience based on recent outcomes
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current performance
            performance = self.get_formula_performance(formula_id, self.learning_window_days)
            
            if performance['total_predictions'] < self.min_predictions_for_learning:
                logger.info(f"Formula {formula_id} has insufficient predictions for learning ({performance['total_predictions']} < {self.min_predictions_for_learning})")
                return True  # Not an error, just not enough data
            
            # Get current experience
            current_exp = self.get_current_formula_experience(formula_id)
            
            # Calculate new values
            new_total_tests = performance['total_predictions']
            new_wins = performance['wins']
            new_losses = performance['losses']
            new_success_rate = performance['success_rate']
            
            # Get base confidence from formula_master
            base_confidence = self.get_formula_base_confidence(formula_id)
            
            # Calculate experience-adjusted confidence
            exp_adjusted_confidence = self.calculate_experience_adjusted_confidence(
                base_confidence, new_success_rate, new_total_tests
            )
            
            # Update or insert formula experience
            if current_exp:
                # Update existing record
                query = """
                    UPDATE formula_experience
                    SET total_tests = %s, wins = %s, losses = %s, success_rate = %s,
                        experience_adjusted_confidence = %s, last_updated = %s
                    WHERE formula_id = %s
                """
                
                params = (
                    new_total_tests, new_wins, new_losses, new_success_rate,
                    exp_adjusted_confidence, datetime.now(), formula_id
                )
                
                success = self.db.execute_query(query, params)
                
                if success:
                    logger.info(f"Updated formula experience for {formula_id}: "
                              f"success_rate={new_success_rate}%, adjusted_confidence={exp_adjusted_confidence}")
                    
                    # Log AI event
                    self.log_ai_event(
                        event_type="FORMULA_LEARNING_UPDATED",
                        description=f"Formula {formula_id} learning updated: success_rate={new_success_rate}%, adjusted_confidence={exp_adjusted_confidence}"
                    )
                    
                    return True
                else:
                    logger.error(f"Failed to update formula experience for {formula_id}")
                    return False
            else:
                # Insert new record
                query = """
                    INSERT INTO formula_experience 
                    (formula_id, total_tests, wins, losses, success_rate, experience_adjusted_confidence, last_updated)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                
                params = (
                    formula_id, new_total_tests, new_wins, new_losses,
                    new_success_rate, exp_adjusted_confidence, datetime.now()
                )
                
                success = self.db.execute_query(query, params)
                
                if success:
                    logger.info(f"Created formula experience for {formula_id}: "
                              f"success_rate={new_success_rate}%, adjusted_confidence={exp_adjusted_confidence}")
                    
                    # Log AI event
                    self.log_ai_event(
                        event_type="FORMULA_LEARNING_CREATED",
                        description=f"Formula {formula_id} learning created: success_rate={new_success_rate}%, adjusted_confidence={exp_adjusted_confidence}"
                    )
                    
                    return True
                else:
                    logger.error(f"Failed to create formula experience for {formula_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error updating formula experience for {formula_id}: {e}")
            return False
    
    def get_formula_base_confidence(self, formula_id: str) -> float:
        """Get base confidence from formula_master table"""
        try:
            query = """
                SELECT confidence_threshold
                FROM formula_master
                WHERE id = %s
            """
            
            result = self.db.fetch_one(query, (formula_id,))
            
            if result:
                return result[0] or 0.5
            else:
                logger.warning(f"Formula {formula_id} not found in formula_master")
                return 0.5  # Default confidence
                
        except Exception as e:
            logger.error(f"Error getting base confidence for formula {formula_id}: {e}")
            return 0.5
    
    def get_all_active_formulas(self) -> List[str]:
        """Get all active formula IDs"""
        try:
            query = """
                SELECT id
                FROM formula_master
                WHERE is_active = TRUE
                ORDER BY id
            """
            
            results = self.db.fetch_query(query)
            
            formula_ids = [row[0] for row in results]
            logger.info(f"Found {len(formula_ids)} active formulas for learning")
            return formula_ids
            
        except Exception as e:
            logger.error(f"Error getting active formulas: {e}")
            return []
    
    def update_all_formula_learning(self) -> int:
        """
        Update learning for all active formulas
        
        Returns:
            Number of formulas updated
        """
        try:
            formula_ids = self.get_all_active_formulas()
            formulas_updated = 0
            
            for formula_id in formula_ids:
                if self.update_formula_experience(formula_id):
                    formulas_updated += 1
            
            logger.info(f"Learning update completed. Updated {formulas_updated}/{len(formula_ids)} formulas")
            return formulas_updated
            
        except Exception as e:
            logger.error(f"Error in learning update: {e}")
            return 0
    
    def get_learning_statistics(self) -> Dict:
        """Get overall learning statistics"""
        try:
            query = """
                SELECT 
                    COUNT(*) as total_formulas,
                    SUM(total_tests) as total_predictions,
                    SUM(wins) as total_wins,
                    AVG(success_rate) as avg_success_rate,
                    AVG(experience_adjusted_confidence) as avg_adjusted_confidence
                FROM formula_experience
            """
            
            result = self.db.fetch_one(query)
            
            if result:
                return {
                    'total_formulas_with_experience': result[0] or 0,
                    'total_predictions_tracked': result[1] or 0,
                    'total_wins': result[2] or 0,
                    'avg_success_rate': round(result[3] or 0.0, 2),
                    'avg_adjusted_confidence': round(result[4] or 0.0, 3),
                    'learning_window_days': self.learning_window_days
                }
            else:
                return {
                    'total_formulas_with_experience': 0,
                    'total_predictions_tracked': 0,
                    'total_wins': 0,
                    'avg_success_rate': 0.0,
                    'avg_adjusted_confidence': 0.0,
                    'learning_window_days': self.learning_window_days
                }
                
        except Exception as e:
            logger.error(f"Error getting learning statistics: {e}")
            return {
                'total_formulas_with_experience': 0,
                'total_predictions_tracked': 0,
                'total_wins': 0,
                'avg_success_rate': 0.0,
                'avg_adjusted_confidence': 0.0,
                'learning_window_days': self.learning_window_days
            }
    
    def log_ai_event(self, event_type: str, description: str):
        """Log AI events to ai_event_log table"""
        try:
            query = """
                INSERT INTO ai_event_log (event_type, description)
                VALUES (%s, %s)
            """
            
            params = (event_type, description)
            self.db.execute_query(query, params)
            
        except Exception as e:
            logger.error(f"Error logging AI event: {e}")

# Global learning engine instance
ai_learning_engine = AILearningEngine()
