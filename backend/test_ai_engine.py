#!/usr/bin/env python3

from app.services.ai_signal_engine import ai_signal_engine

def test_ai_signal_engine():
    """Test the AI signal engine"""
    
    print('Testing AI signal engine...')
    
    # Get market snapshot
    market_data = ai_signal_engine.get_latest_market_snapshot()
    if market_data:
        print(f'Market data: {market_data}')
    else:
        print('No market data found')
    
    # Get active formulas  
    formulas = ai_signal_engine.get_active_formulas()
    print(f'Active formulas: {len(formulas)} found')
    for formula in formulas:
        print(f'  - {formula["id"]}: {formula["name"]} ({formula["type"]})')
    
    # Test signal generation
    signals = ai_signal_engine.generate_signals()
    print(f'Signals generated: {signals}')

if __name__ == "__main__":
    test_ai_signal_engine()
