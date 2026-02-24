#!/usr/bin/env python3
"""
Create a minimal instruments.json file for NIFTY and BANKNIFTY options
This is a fallback when the Upstox instruments API fails
"""

import json
from pathlib import Path

def create_minimal_instruments():
    """Create minimal instruments.json with NIFTY and BANKNIFTY options"""
    
    # Create data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Generate sample instrument keys for common strikes
    instruments = []
    symbols = ["NIFTY", "BANKNIFTY"]
    
    # Common strike ranges
    nifty_strikes = list(range(19000, 21001, 50))  # 19000 to 21000, step 50
    banknifty_strikes = list(range(41000, 46001, 100))  # 41000 to 46000, step 100
    
    for symbol in symbols:
        strikes = nifty_strikes if symbol == "NIFTY" else banknifty_strikes
        
        for strike in strikes:
            # Call option
            instruments.append({
                "instrument_key": f"NSE_FO|{symbol}|{strike}|CE",
                "exchange": "NSE_FO",
                "tradingsymbol": f"{symbol}{strike}CE",
                "name": symbol,
                "last_price": 0,
                "expiry": "2026-02-26",
                "strike": strike,
                "tick_size": 0.05,
                "lot_size": 50 if symbol == "NIFTY" else 25,
                "instrument_type": "CE",
                "segment": "NSE_FO",
                "exchange_token": f"{symbol}_{strike}_CE"
            })
            
            # Put option
            instruments.append({
                "instrument_key": f"NSE_FO|{symbol}|{strike}|PE",
                "exchange": "NSE_FO",
                "tradingsymbol": f"{symbol}{strike}PE",
                "name": symbol,
                "last_price": 0,
                "expiry": "2026-02-26",
                "strike": strike,
                "tick_size": 0.05,
                "lot_size": 50 if symbol == "NIFTY" else 25,
                "instrument_type": "PE",
                "segment": "NSE_FO",
                "exchange_token": f"{symbol}_{strike}_PE"
            })
    
    # Save to file
    instruments_file = data_dir / "instruments.json"
    with open(instruments_file, 'w', encoding='utf-8') as f:
        json.dump(instruments, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Created minimal instruments.json with {len(instruments)} instruments")
    print(f"   NIFTY: {len(nifty_strikes) * 2} options")
    print(f"   BANKNIFTY: {len(banknifty_strikes) * 2} options")

if __name__ == "__main__":
    create_minimal_instruments()
