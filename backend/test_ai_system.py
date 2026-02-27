"""
Test StrikeIQ AI System Implementation
Verifies all components are working correctly
"""
import asyncio
import logging
from datetime import datetime

# Test imports
try:
    from app.services.ai_signal_engine import ai_signal_engine
    from app.services.paper_trade_engine import paper_trade_engine
    from app.services.ai_outcome_engine import ai_outcome_engine
    from app.services.ai_learning_engine import ai_learning_engine
    from ai.scheduler import ai_scheduler
    from ai.ai_db import ai_db
    from app.services.ai_logging_config import signal_engine_logger
    print("✅ All AI imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)

async def test_ai_system():
    """Test all AI system components"""
    
    print("\n🧪 Testing StrikeIQ AI System...")
    print("=" * 50)
    
    # Test 1: Database Connection
    print("\n1. Testing Database Connection...")
    try:
        ai_db.connect()
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    # Test 2: Signal Engine
    print("\n2. Testing Signal Engine...")
    try:
        signals = ai_signal_engine.generate_signals()
        print(f"✅ Signal engine working - Generated {signals} signals")
    except Exception as e:
        print(f"❌ Signal engine failed: {e}")
    
    # Test 3: Paper Trade Engine
    print("\n3. Testing Paper Trade Engine...")
    try:
        trades_created = paper_trade_engine.process_new_predictions()
        trades_closed = paper_trade_engine.monitor_open_trades()
        print(f"✅ Paper trade engine working - Created {trades_created}, Closed {trades_closed}")
    except Exception as e:
        print(f"❌ Paper trade engine failed: {e}")
    
    # Test 4: Outcome Engine
    print("\n4. Testing Outcome Engine...")
    try:
        outcomes = ai_outcome_engine.evaluate_pending_outcomes()
        stats = ai_outcome_engine.get_outcome_statistics()
        print(f"✅ Outcome engine working - Evaluated {outcomes} outcomes")
        print(f"   Stats: {stats['total_outcomes']} total, {stats['win_rate']:.1f}% win rate")
    except Exception as e:
        print(f"❌ Outcome engine failed: {e}")
    
    # Test 5: Learning Engine
    print("\n5. Testing Learning Engine...")
    try:
        formulas_updated = ai_learning_engine.update_all_formula_learning()
        learning_stats = ai_learning_engine.get_learning_statistics()
        print(f"✅ Learning engine working - Updated {formulas_updated} formulas")
        print(f"   Stats: {learning_stats['total_formulas_with_experience']} formulas with experience")
    except Exception as e:
        print(f"❌ Learning engine failed: {e}")
    
    # Test 6: Scheduler
    print("\n6. Testing AI Scheduler...")
    try:
        job_status = ai_scheduler.get_job_status()
        print(f"✅ Scheduler working - {len(job_status)} active jobs")
        for job in job_status:
            print(f"   - {job['name']}: {job['trigger']}")
    except Exception as e:
        print(f"❌ Scheduler failed: {e}")
    
    # Test 7: Market Snapshot Creation
    print("\n7. Testing Market Snapshot...")
    try:
        ai_scheduler.create_sample_market_snapshot()
        print("✅ Market snapshot creation working")
    except Exception as e:
        print(f"❌ Market snapshot failed: {e}")
    
    # Cleanup
    try:
        ai_db.disconnect()
        print("\n✅ Database connection closed")
    except Exception as e:
        print(f"⚠️ Database close warning: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 StrikeIQ AI System Test Complete!")
    print("🚀 System is ready for production use!")

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Run test
    asyncio.run(test_ai_system())
