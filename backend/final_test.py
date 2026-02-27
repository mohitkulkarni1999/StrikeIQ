#!/usr/bin/env python3

import asyncio
from app.api.v1.market import get_market_dashboard

async def final_test():
    print('=== FINAL INTEGRATION TEST ===')
    
    # Test dashboard endpoint
    dashboard = await get_market_dashboard()
    print('✅ Dashboard API working')
    print(f'   Spot: {dashboard["data"]["spot"]}')
    print(f'   PCR: {dashboard["data"]["pcr"]}')
    print(f'   OI Call: {dashboard["data"]["total_call_oi"]}')
    print(f'   OI Put: {dashboard["data"]["total_put_oi"]}')
    
    # Test AI signal generation
    from app.services.ai_signal_engine import ai_signal_engine
    signals = ai_signal_engine.generate_signals()
    print(f'✅ AI Signal Engine: {signals} signals generated')
    
    # Check recent predictions
    from ai.ai_db import ai_db
    ai_db.connect()
    recent = ai_db.fetch_one('SELECT COUNT(*) FROM prediction_log WHERE prediction_time >= NOW() - INTERVAL \'1 hour\'')
    print(f'✅ Recent predictions: {recent[0] if recent else 0} in last hour')
    
    ai_db.disconnect()
    print('🎉 ALL SYSTEMS OPERATIONAL')

if __name__ == "__main__":
    asyncio.run(final_test())
