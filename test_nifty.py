from backend.app.services.market_dashboard_service import MarketDashboardService
from backend.app.core.config import settings
import asyncio

async def test_nifty():
    print("Testing NIFTY API with correct instrument keys...")
    
    # Initialize service with mock db
    service = MarketDashboardService(db=None)
    
    # Test with correct NIFTY 50 key
    try:
        result = await service.get_dashboard_data("NIFTY")
        print(f"Result for NIFTY50: {result}")
        
        if result.get('current_market', {}).get('spot_price'):
            print(f"✅ SUCCESS: Found NIFTY data!")
            print(f"Spot Price: {result['current_market']['spot_price']}")
        else:
            print("❌ No spot price found")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_nifty())
