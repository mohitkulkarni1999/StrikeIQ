from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
from .outcome_checker import outcome_checker

logger = logging.getLogger(__name__)

class AIScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.setup_jobs()
        
    def setup_jobs(self):
        """Setup scheduled jobs for AI learning system"""
        try:
            # Signal generation job → every 5 seconds
            self.scheduler.add_job(
                func=self.signal_generation_job,
                trigger=IntervalTrigger(seconds=5),
                id='signal_generation',
                name='Generate AI signals',
                replace_existing=True,
                max_instances=1  # Prevent overlapping
            )
            
            # Paper trade monitor → every 10 seconds
            self.scheduler.add_job(
                func=self.paper_trade_monitor_job,
                trigger=IntervalTrigger(seconds=10),
                id='paper_trade_monitor',
                name='Monitor paper trades',
                replace_existing=True,
                max_instances=1  # Prevent overlapping
            )
            
            # New prediction processing → every 15 seconds
            self.scheduler.add_job(
                func=self.new_prediction_processing_job,
                trigger=IntervalTrigger(seconds=15),
                id='new_prediction_processing',
                name='Process new predictions',
                replace_existing=True,
                max_instances=1  # Prevent overlapping
            )
            
            # Outcome checker → every 1 minute
            self.scheduler.add_job(
                func=self.outcome_checker_job,
                trigger=IntervalTrigger(minutes=1),
                id='outcome_checker',
                name='Check prediction outcomes',
                replace_existing=True,
                max_instances=1  # Prevent overlapping
            )
            
            # Learning updater → every 1 minute
            self.scheduler.add_job(
                func=self.learning_update_job,
                trigger=IntervalTrigger(minutes=1),
                id='learning_update',
                name='Update AI learning',
                replace_existing=True,
                max_instances=1  # Prevent overlapping
            )
            
            # Market snapshot collector → every 30 seconds
            self.scheduler.add_job(
                func=self.market_snapshot_job,
                trigger=IntervalTrigger(seconds=30),
                id='market_snapshot',
                name='Collect market snapshots',
                replace_existing=True,
                max_instances=1  # Prevent overlapping
            )
            
            logger.info("AI scheduler jobs setup completed")
            
        except Exception as e:
            logger.error(f"Error setting up scheduler jobs: {e}")
    
    def signal_generation_job(self):
        """Job for generating AI signals"""
        try:
            from app.services.ai_signal_engine import ai_signal_engine
            signals_generated = ai_signal_engine.generate_signals()
            if signals_generated > 0:
                logger.info(f"Signal generation job: {signals_generated} signals generated")
        except Exception as e:
            logger.error(f"Error in signal generation job: {e}")
    
    def paper_trade_monitor_job(self):
        """Job for monitoring paper trades"""
        try:
            from app.services.paper_trade_engine import paper_trade_engine
            trades_closed = paper_trade_engine.monitor_open_trades()
            if trades_closed > 0:
                logger.info(f"Paper trade monitor job: {trades_closed} trades closed")
        except Exception as e:
            logger.error(f"Error in paper trade monitor job: {e}")
    
    def new_prediction_processing_job(self):
        """Job for processing new predictions into paper trades"""
        try:
            from app.services.paper_trade_engine import paper_trade_engine
            trades_created = paper_trade_engine.process_new_predictions()
            if trades_created > 0:
                logger.info(f"New prediction processing job: {trades_created} trades created")
        except Exception as e:
            logger.error(f"Error in new prediction processing job: {e}")
    
    def outcome_checker_job(self):
        """Job for checking prediction outcomes"""
        try:
            from app.services.ai_outcome_engine import ai_outcome_engine
            outcomes_evaluated = ai_outcome_engine.evaluate_pending_outcomes()
            if outcomes_evaluated > 0:
                logger.info(f"Outcome checker job: {outcomes_evaluated} outcomes evaluated")
        except Exception as e:
            logger.error(f"Error in outcome checker job: {e}")
    
    def learning_update_job(self):
        """Job for updating AI learning"""
        try:
            from app.services.ai_learning_engine import ai_learning_engine
            formulas_updated = ai_learning_engine.update_all_formula_learning()
            if formulas_updated > 0:
                logger.info(f"Learning update job: {formulas_updated} formulas updated")
        except Exception as e:
            logger.error(f"Error in learning update job: {e}")
    
    def market_snapshot_job(self):
        """Job for collecting market snapshots"""
        try:
            # This would collect real market data
            # For now, create sample snapshots
            self.create_sample_market_snapshot()
        except Exception as e:
            logger.error(f"Error in market snapshot job: {e}")
    
    def create_sample_market_snapshot(self):
        """Create sample market snapshot for AI analysis"""
        try:
            import random
            
            # Sample market data (in production, fetch from real market)
            spot_price = random.uniform(19500, 20500)
            total_call_oi = random.uniform(1000000, 5000000)
            total_put_oi = random.uniform(800000, 4000000)
            pcr = total_put_oi / total_call_oi if total_call_oi > 0 else 1.0
            atm_strike = round(spot_price / 50) * 50
            
            from ai.ai_db import ai_db
            
            query = """
                INSERT INTO market_snapshot 
                (symbol, spot_price, pcr, total_call_oi, total_put_oi, atm_strike)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            params = ("NIFTY", spot_price, pcr, total_call_oi, total_put_oi, atm_strike)
            ai_db.execute_query(query, params)
            
        except Exception as e:
            logger.error(f"Error creating sample market snapshot: {e}")
            
    def start(self):
        """Start the scheduler"""
        try:
            self.scheduler.start()
            logger.info("AI scheduler started successfully")
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            
    def stop(self):
        """Stop the scheduler"""
        try:
            self.scheduler.shutdown()
            logger.info("AI scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
            
    def get_job_status(self):
        """Get status of all scheduled jobs"""
        try:
            # Start scheduler if not running
            if not self.scheduler.running:
                self.scheduler.start()
                
            jobs = []
            for job in self.scheduler.get_jobs():
                jobs.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': str(job.next_run_time) if job.next_run_time else None,
                    'trigger': str(job.trigger)
                })
            return jobs
        except Exception as e:
            logger.error(f"Error getting job status: {e}")
            return []

# Global scheduler instance
ai_scheduler = AIScheduler()
