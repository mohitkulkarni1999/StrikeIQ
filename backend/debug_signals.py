#!/usr/bin/env python3

from app.services.ai_signal_engine import ai_signal_engine

def debug_signal_generation():
    """Debug why no signals are being generated"""
    
    print('=== DEBUGGING SIGNAL GENERATION ===')
    
    # Get market snapshot
    market_data = ai_signal_engine.get_latest_market_snapshot()
    if not market_data:
        print('❌ No market data available')
        return
    
    print(f'✅ Market data: PCR={market_data["pcr"]:.3f}, Spot={market_data["spot_price"]:.2f}')
    
    # Get active formulas  
    formulas = ai_signal_engine.get_active_formulas()
    print(f'✅ Found {len(formulas)} active formulas')
    
    # Test each formula individually
    for i, formula in enumerate(formulas[:3]):  # Test first 3 formulas
        print(f'\n--- Testing Formula {i+1}: {formula["id"]} ---')
        print(f'Name: {formula["name"]}')
        print(f'Conditions: {formula["conditions"]}')
        print(f'Confidence Threshold: {formula["confidence_threshold"]}')
        
        # Evaluate conditions
        matches, signal, confidence = ai_signal_engine.evaluate_formula_conditions(
            formula, market_data
        )
        
        print(f'Result: matches={matches}, signal={signal}, confidence={confidence:.3f}')
        
        if matches:
            print(f'🎯 SIGNAL WOULD BE GENERATED: {signal} @ {confidence:.3f}')
        else:
            print('❌ No signal - conditions not met')

if __name__ == "__main__":
    debug_signal_generation()
