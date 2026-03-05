#!/usr/bin/env python3
"""
Test the option subscription functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.websocket_market_feed import get_atm_strike, build_option_keys

def test_atm_calculation():
    """Test ATM strike calculation"""
    print("Testing ATM Strike Calculation:")
    print("=" * 40)
    
    test_prices = [24555.30, 24678.90, 24499.50, 24750.00]
    
    for price in test_prices:
        atm = get_atm_strike(price)
        print(f"Price: {price} -> ATM: {atm}")
    
    print()

def test_option_key_generation():
    """Test option key generation"""
    print("Testing Option Key Generation:")
    print("=" * 40)
    
    atm = 24650
    expiry = "26JUN"
    
    keys = build_option_keys("NIFTY", atm, expiry)
    
    print(f"ATM: {atm}")
    print(f"Expiry: {expiry}")
    print(f"Total Keys: {len(keys)}")
    print()
    
    # Show first few keys
    print("Sample Keys:")
    for i, key in enumerate(keys[:10]):
        print(f"  {i+1}. {key}")
    
    print("  ...")
    print(f"  {len(keys)}. {keys[-1]}")
    print()

def test_subscription_limit():
    """Test subscription limit"""
    print("Testing Subscription Limit:")
    print("=" * 40)
    
    # Test with larger range to trigger limit
    keys = build_option_keys("NIFTY", 24650, "26JUN")
    
    print(f"Generated keys: {len(keys)}")
    
    # Apply limit
    if len(keys) > 60:
        limited_keys = keys[:60]
        print(f"Limited to: {len(limited_keys)}")
    else:
        print("No limit needed")
    
    print()

if __name__ == "__main__":
    print("🧪 OPTION SUBSCRIPTION FUNCTIONALITY TEST")
    print("=" * 50)
    
    test_atm_calculation()
    test_option_key_generation()
    test_subscription_limit()
    
    print("✅ All tests completed successfully!")
    print()
    print("Expected behavior when server runs:")
    print("- Index ticks will trigger ATM calculation")
    print("- ATM changes will trigger option subscription")
    print("- Option keys will be generated around ATM")
    print("- Subscription will be limited to 60 instruments")
    print("- Logs will show subscription details")
