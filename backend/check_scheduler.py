#!/usr/bin/env python3

from ai.scheduler import ai_scheduler

def check_scheduler():
    """Check scheduler job status"""
    
    jobs = ai_scheduler.get_job_status()
    print('Scheduler jobs:')
    for job in jobs:
        print(f'  - {job["id"]}: {job["name"]} (next: {job["next_run_time"]})')
    
    print(f'Total jobs: {len(jobs)}')

if __name__ == "__main__":
    check_scheduler()
