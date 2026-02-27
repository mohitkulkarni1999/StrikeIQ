#!/usr/bin/env python3

from app.services.ai_signal_engine import ai_signal_engine

def debug_f14():
    """Debug why F14 formula isn't triggering"""
    
    # Get market data
    market_data = ai_signal_engine.get_latest_market_snapshot()
    print(f'Market PCR: {market_data["pcr"]}')
    
    # Get F14 specifically
    formulas = ai_signal_engine.get_active_formulas()
    f14 = next((f for f in formulas if f['id'] == 'F14'), None)
    
    if f14:
        print(f'F14 conditions: {f14["conditions"]}')
        print(f'F14 confidence threshold: {f14["confidence_threshold"]}')
        
        # Test evaluation
        matches, signal, confidence = ai_signal_engine.evaluate_formula_conditions(f14, market_data)
        print(f'Evaluation: matches={matches}, signal={signal}, confidence={confidence}')
        
        # Manual check
        pcr = market_data.get('pcr', 0)
        print(f'Manual check: PCR={pcr} < 0.8 = {pcr < 0.8}')
    else:
        print('F14 not found in active formulas')

if __name__ == "__main__":
    debug_f14()
