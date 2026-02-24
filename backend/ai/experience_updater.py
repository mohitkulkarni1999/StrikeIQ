import logging
from datetime import datetime
from typing import Optional
from .ai_db import ai_db

logger = logging.getLogger(__name__)

class ExperienceUpdater:
    def __init__(self):
        self.db = ai_db
        
    def get_formula_experience(self, formula_id: str) -> Optional[dict]:
        """Get current experience statistics for a formula"""
        try:
            query = """
                SELECT total_tests, wins, losses, success_rate
                FROM formula_experience
                WHERE formula_id = %s
            """
            
            result = self.db.fetch_one(query, (formula_id,))
            
            if result:
                return {
                    'total_tests': result[0],
                    'wins': result[1],
                    'losses': result[2],
                    'success_rate': result[3]
                }
            else:
                # Initialize new formula experience
                self.initialize_formula_experience(formula_id)
                return {
                    'total_tests': 0,
                    'wins': 0,
                    'losses': 0,
                    'success_rate': 0.0
                }
                
        except Exception as e:
            logger.error(f"Error getting formula experience for {formula_id}: {e}")
            return None
            
    def initialize_formula_experience(self, formula_id: str):
        """Initialize experience record for a new formula"""
        try:
            query = """
                INSERT INTO formula_experience 
                (formula_id, total_tests, wins, losses, success_rate, last_updated)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            params = (
                formula_id,
                0,  # total_tests
                0,  # wins
                0,  # losses
                0.0,  # success_rate
                datetime.now()  # last_updated
            )
            
            success = self.db.execute_query(query, params)
            
            if success:
                logger.info(f"Initialized experience for formula {formula_id}")
            else:
                logger.error(f"Failed to initialize experience for formula {formula_id}")
                
        except Exception as e:
            logger.error(f"Error initializing formula experience: {e}")
            
    def update_experience(self, formula_id: str, outcome: str):
        """
        Update experience statistics for a formula based on prediction outcome
        
        Args:
            formula_id: Formula identifier (e.g., F01, F02, etc.)
            outcome: Prediction outcome (WIN/LOSS/NEUTRAL)
        """
        try:
            # Get current experience
            experience = self.get_formula_experience(formula_id)
            
            if not experience:
                logger.error(f"Could not get experience for formula {formula_id}")
                return False
                
            # Update counters based on outcome
            total_tests = experience['total_tests'] + 1
            wins = experience['wins']
            losses = experience['losses']
            
            if outcome == 'WIN':
                wins += 1
            elif outcome == 'LOSS':
                losses += 1
            # NEUTRAL doesn't increment wins or losses
            
            # Calculate new success rate
            success_rate = (wins / total_tests) * 100 if total_tests > 0 else 0.0
            
            # Update database
            query = """
                UPDATE formula_experience
                SET total_tests = %s,
                    wins = %s,
                    losses = %s,
                    success_rate = %s,
                    last_updated = %s
                WHERE formula_id = %s
            """
            
            params = (
                total_tests,
                wins,
                losses,
                success_rate,
                datetime.now(),
                formula_id
            )
            
            success = self.db.execute_query(query, params)
            
            if success:
                logger.info(f"Updated experience for {formula_id}: {outcome} -> {total_tests} tests, {wins} wins, {losses} losses, {success_rate:.2f}% success rate")
                return True
            else:
                logger.error(f"Failed to update experience for formula {formula_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating experience for {formula_id}: {e}")
            return False
            
    def get_top_performers(self, limit: int = 10) -> list:
        """Get top performing formulas based on success rate"""
        try:
            query = """
                SELECT formula_id, total_tests, wins, losses, success_rate
                FROM formula_experience
                WHERE total_tests >= 10  -- Only include formulas with sufficient data
                ORDER BY success_rate DESC, total_tests DESC
                LIMIT %s
            """
            
            results = self.db.fetch_query(query, (limit,))
            
            performers = []
            for row in results:
                performers.append({
                    'formula_id': row[0],
                    'total_tests': row[1],
                    'wins': row[2],
                    'losses': row[3],
                    'success_rate': row[4]
                })
                
            logger.info(f"Retrieved top {len(performers)} performing formulas")
            return performers
            
        except Exception as e:
            logger.error(f"Error getting top performers: {e}")
            return []

# Global experience updater instance
experience_updater = ExperienceUpdater()
