import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict
from .prediction_service import prediction_service
from .experience_updater import experience_updater

logger = logging.getLogger(__name__)

class OutcomeChecker:
    def __init__(self):
        self.prediction_service = prediction_service
        self.experience_updater = experience_updater
        
    def get_current_nifty_price(self) -> float:
        """Get current NIFTY price from Upstox API"""
        try:
            # Use existing Upstox API endpoint
            url = "https://api.upstox.com/v2/market-quote/ltp"
            headers = {
                'accept': 'application/json',
                'Authorization': 'Bearer ' + self._get_access_token()
            }
            params = {
                'instrument_key': 'NSE_INDEX|Nifty 50'
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'ltp' in data['data']:
                    price = float(data['data']['ltp'])
                    logger.info(f"Current NIFTY price: {price}")
                    return price
                    
            logger.error(f"Failed to get NIFTY price: {response.status_code} - {response.text}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting NIFTY price: {e}")
            return None
            
    def _get_access_token(self) -> str:
        """Get access token from credentials file"""
        try:
            import json
            with open('upstox_credentials.json', 'r') as f:
                credentials = json.load(f)
                return credentials.get('access_token', '')
        except Exception as e:
            logger.error(f"Error reading access token: {e}")
            return ''
            
    def calculate_outcome(self, initial_spot: float, current_spot: float) -> str:
        """
        Calculate prediction outcome based on price movement
        
        Args:
            initial_spot: NIFTY spot when prediction was made
            current_spot: Current NIFTY spot
            
        Returns:
            WIN, LOSS, or NEUTRAL
        """
        if not initial_spot or not current_spot:
            return 'NEUTRAL'
            
        price_change = ((current_spot - initial_spot) / initial_spot) * 100
        
        if price_change > 0.3:
            return 'WIN'
        elif price_change < -0.3:
            return 'LOSS'
        else:
            return 'NEUTRAL'
            
    def check_outcomes(self):
        """Check outcomes for all pending predictions"""
        try:
            logger.info("Starting outcome check cycle")
            
            # Get all predictions that are ready for outcome checking
            pending_predictions = self.prediction_service.get_pending_predictions()
            
            if not pending_predictions:
                logger.info("No pending predictions to check")
                return
                
            current_price = self.get_current_nifty_price()
            
            if not current_price:
                logger.error("Could not get current NIFTY price, skipping outcome check")
                return
                
            for prediction in pending_predictions:
                try:
                    # Calculate outcome
                    outcome = self.calculate_outcome(
                        prediction['nifty_spot'],
                        current_price
                    )
                    
                    logger.info(f"Prediction {prediction['id']}: {prediction['signal']} @ {prediction['nifty_spot']} -> {outcome} (current: {current_price})")
                    
                    # Mark prediction as checked
                    success = self.prediction_service.mark_prediction_checked(
                        prediction['id'],
                        outcome
                    )
                    
                    if success:
                        # Update formula experience
                        self.experience_updater.update_experience(
                            prediction['formula_id'],
                            outcome
                        )
                        
                except Exception as e:
                    logger.error(f"Error processing prediction {prediction['id']}: {e}")
                    continue
                    
            logger.info(f"Outcome check cycle completed. Processed {len(pending_predictions)} predictions")
            
        except Exception as e:
            logger.error(f"Error in outcome check cycle: {e}")

# Global outcome checker instance
outcome_checker = OutcomeChecker()
