import logging
from typing import Optional
from .ai_db import ai_db

logger = logging.getLogger(__name__)

class ExperienceService:
    """
    Service to retrieve and manage formula experience scores
    for confidence adjustment in AI decision pipeline
    """
    
    def __init__(self):
        self.db = ai_db
        
    def get_experience_score(self, formula_id: str) -> float:
        """
        Get experience score (success_rate) for a formula
        
        Args:
            formula_id: Formula identifier (e.g., 'F01', 'F02', ..., 'F24')
            
        Returns:
            float: Success rate (0.0 to 1.0), default 0.5 if no record exists
        """
        try:
            query = """
                SELECT success_rate
                FROM formula_experience
                WHERE formula_id = %s
            """
            
            result = self.db.fetch_one(query, (formula_id,))
            
            if result:
                success_rate = float(result[0])
                logger.info(f"Experience score for {formula_id}: {success_rate:.3f}")
                return success_rate
            else:
                logger.info(f"No experience record for {formula_id}, using default 0.5")
                return 0.5  # Default for new formulas
                
        except Exception as e:
            logger.error(f"Error getting experience score for {formula_id}: {e}")
            return 0.5  # Safe default on error
            
    def get_all_experience_scores(self) -> dict:
        """
        Get experience scores for all formulas
        
        Returns:
            dict: Mapping of formula_id -> success_rate
        """
        try:
            query = """
                SELECT formula_id, success_rate
                FROM formula_experience
                WHERE total_tests >= 5  -- Only include formulas with sufficient data
            """
            
            results = self.db.fetch_query(query)
            
            scores = {}
            for row in results:
                formula_id = row[0]
                success_rate = float(row[1])
                scores[formula_id] = success_rate
                
            logger.info(f"Retrieved experience scores for {len(scores)} formulas")
            return scores
            
        except Exception as e:
            logger.error(f"Error getting all experience scores: {e}")
            return {}
            
    def is_formula_trustworthy(self, formula_id: str, min_tests: int = 10) -> bool:
        """
        Check if a formula has sufficient experience to be trustworthy
        
        Args:
            formula_id: Formula identifier
            min_tests: Minimum number of tests required
            
        Returns:
            bool: True if formula has sufficient experience
        """
        try:
            query = """
                SELECT total_tests
                FROM formula_experience
                WHERE formula_id = %s
            """
            
            result = self.db.fetch_one(query, (formula_id,))
            
            if result:
                total_tests = int(result[0])
                is_trustworthy = total_tests >= min_tests
                logger.info(f"Formula {formula_id} trustworthiness: {total_tests} tests, trustworthy: {is_trustworthy}")
                return is_trustworthy
            else:
                logger.info(f"Formula {formula_id} has no experience record, not trustworthy")
                return False
                
        except Exception as e:
            logger.error(f"Error checking formula trustworthiness for {formula_id}: {e}")
            return False
            
    def get_top_performers(self, limit: int = 5, min_tests: int = 10) -> list:
        """
        Get top performing formulas based on experience
        
        Args:
            limit: Maximum number of formulas to return
            min_tests: Minimum tests required for consideration
            
        Returns:
            list: Top performing formulas with their scores
        """
        try:
            query = """
                SELECT formula_id, success_rate, total_tests, wins, losses
                FROM formula_experience
                WHERE total_tests >= %s
                ORDER BY success_rate DESC, total_tests DESC
                LIMIT %s
            """
            
            results = self.db.fetch_query(query, (min_tests, limit))
            
            performers = []
            for row in results:
                performers.append({
                    'formula_id': row[0],
                    'success_rate': float(row[1]),
                    'total_tests': int(row[2]),
                    'wins': int(row[3]),
                    'losses': int(row[4])
                })
                
            logger.info(f"Top {len(performers)} performing formulas retrieved")
            return performers
            
        except Exception as e:
            logger.error(f"Error getting top performers: {e}")
            return []

# Global experience service instance
experience_service = ExperienceService()
