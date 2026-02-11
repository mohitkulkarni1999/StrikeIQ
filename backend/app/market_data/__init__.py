from apscheduler.schedulers.asyncio import AsyncIOScheduler
from ..services.poller_service import get_poller_service
import logging

_scheduler = AsyncIOScheduler()

async def start_data_scheduler():
    global _scheduler
    try:
        poller = get_poller_service()
        
        # Add job to poll every 5 minutes
        _scheduler.add_job(
            poller.poll_market_data,
            'interval',
            minutes=5,
            id='market_data_poll'
        )
        
        _scheduler.start()
        logging.info("APScheduler: Data collection jobs started")
        
        # Trigger an initial poll immediately in the background
        asyncio.create_task(poller.poll_market_data())
    except Exception as e:
        logging.error(f"Failed to start APScheduler: {e}")

async def stop_data_scheduler():
    global _scheduler
    if _scheduler.running:
        _scheduler.shutdown()
        logging.info("APScheduler: Data collection jobs stopped")

import asyncio
