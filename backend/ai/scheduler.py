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
            # Schedule outcome checking every 1 minute
            self.scheduler.add_job(
                func=outcome_checker.check_outcomes,
                trigger=IntervalTrigger(minutes=1),
                id='outcome_checker',
                name='Check prediction outcomes',
                replace_existing=True
            )
            
            logger.info("AI scheduler jobs setup completed")
            
        except Exception as e:
            logger.error(f"Error setting up scheduler jobs: {e}")
            
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
            jobs = []
            for job in self.scheduler.get_jobs():
                jobs.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time,
                    'trigger': str(job.trigger)
                })
            return jobs
        except Exception as e:
            logger.error(f"Error getting job status: {e}")
            return []

# Global scheduler instance
ai_scheduler = AIScheduler()
