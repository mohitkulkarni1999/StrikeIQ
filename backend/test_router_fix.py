#!/usr/bin/env python3
"""
Test the message router fix
"""

from app.services.message_router import message_router

# Test the fixed router
test_keys = [
    'NSE_INDEX|Nifty 50',
    'NSE_INDEX|Nifty Bank',
    'NSE_FO|NIFTY 26MAR2024 24500 CE'
]

print("Testing Message Router Fix:")
print("=" * 40)

for key in test_keys:
    tick = {'instrument_key': key, 'ltp': 24555.30}
    message = message_router.route_tick(tick)
    if message:
        print(f"✅ {key} -> {message['type']} for {message['symbol']}")
    else:
        print(f"❌ {key} -> Failed to route")

print("=" * 40)
print("Router test completed")
