#!/usr/bin/env python3
"""
Simple test for SmartMoneyEngine v2
"""

import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.models.database import Base, get_db
from app.models.market_data import OptionChainSnapshot
from app.services.market_data.smart_money_engine_v2 import SmartMoneyEngineV2
from app.core.config import settings

def create_simple_test_data(db: Session):
    """Create simple test data"""
    print("Creating simple test data...")
    
    base_time = datetime.now(timezone.utc)
    strikes = [20000]
    
    # Create 15 snapshots (above minimum threshold)
    for i in range(15):
        timestamp = base_time - timedelta(minutes=i*2)
        
        for strike in strikes:
            # CE option
            ce_snapshot = OptionChainSnapshot(
                symbol="NIFTY",
                timestamp=timestamp,
                strike=strike,
                option_type="CE",
                expiry="2026-02-27",
                oi=100000 + i*1000,
                oi_change=1000 + i*100,
                prev_oi=99000 + i*1000,
                oi_delta=1000 + i*100,
                ltp=50.0,
                iv=15.0 + i * 0.1,
                volume=5000 + i*500,
                delta=-0.4,
                gamma=0.001,
                theta=-2.0,
                vega=5.0
            )
            db.add(ce_snapshot)
            
            # PE option
            pe_snapshot = OptionChainSnapshot(
                symbol="NIFTY",
                timestamp=timestamp,
                strike=strike,
                option_type="PE",
                expiry="2026-02-27",
                oi=80000 + i*800,
                oi_change=800 + i*80,
                prev_oi=79200 + i*800,
                oi_delta=800 + i*80,
                ltp=30.0,
                iv=16.0 + i * 0.08,
                volume=4000 + i*400,
                delta=0.3,
                gamma=0.001,
                theta=-1.5,
                vega=4.0
            )
            db.add(pe_snapshot)
    
    db.commit()
    print("Created simple test data")

async def test_v2_simple():
    """Simple test for v2 engine"""
    print("=" * 60)
    print("SmartMoneyEngine v2 Simple Test")
    print("=" * 60)
    
    # Setup database
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    
    # Create session
    db = Session(engine)
    
    try:
        # Create test data
        create_simple_test_data(db)
        
        # Initialize v2 engine
        engine_v2 = SmartMoneyEngineV2(snapshot_count=30, min_snapshots=10)
        
        print("\nTesting NIFTY signal generation...")
        
        # Test NIFTY signal (without saving to performance table)
        nifty_signal = await engine_v2.generate_smart_money_signal("NIFTY", db, save_prediction=False)
        
        print("✅ NIFTY v2 Signal Generated:")
        print(f"   Symbol: {nifty_signal['symbol']}")
        print(f"   Bias: {nifty_signal['bias']}")
        print(f"   Confidence: {nifty_signal['confidence']}")
        
        print("\n📊 Normalized Metrics:")
        for key, value in nifty_signal['metrics'].items():
            print(f"   {key}: {value}")
        
        print("\n💡 Reasoning:")
        for reason in nifty_signal['reasoning']:
            print(f"   - {reason}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    success = asyncio.run(test_v2_simple())
    if success:
        print("\n🎉 SIMPLE V2 TEST PASSED!")
    else:
        print("\n❌ SIMPLE V2 TEST FAILED!")
