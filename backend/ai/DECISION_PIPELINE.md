"""
AI Experience-Based Decision Pipeline

This file demonstrates the complete AI decision flow with experience-based confidence adjustment.

## Decision Flow

1. **Formula generates signal** with original confidence
2. **Experience score fetched** from formula_experience table
3. **Confidence adjusted**: adjusted_confidence = original_confidence * experience_score
4. **Decision filter**: If adjusted_confidence < 0.40 → signal ignored
5. **Strong signals stored** with adjusted confidence in prediction_log

## Example Usage

```python
from ai.formula_integrator import store_formula_signal

# Formula F01 generates signal
success = store_formula_signal(
    formula_id='F01',
    signal='BUY',
    confidence=0.85,      # Original confidence from formula
    current_price=19500.50   # Current NIFTY price
)

# Decision Flow:
# 1. Get experience_score for F01 (e.g., 0.60 = 60% success rate)
# 2. Calculate: 0.85 * 0.60 = 0.51 (adjusted confidence)
# 3. Check: 0.51 >= 0.40 → signal passes filter
# 4. Store: F01 BUY @ 19500.50 with confidence 0.51
```

## Logging Examples

**Signal Stored:**
```
INFO: Formula F01: original confidence=0.85, experience_score=0.600
INFO: Formula F01: adjusted confidence=0.510 (confidence * experience_score)
INFO: Formula signal stored: F01 BUY @ 19500.50 (adjusted_confidence: 0.510)
```

**Signal Ignored:**
```
INFO: Formula F03: original confidence=0.60, experience_score=0.300
INFO: Formula F03: adjusted confidence=0.180 (confidence * experience_score)
WARNING: F03 BUY ignored due to low adjusted confidence 0.18
```

## Experience Score Impact

| Formula | Success Rate | Original Conf | Adjusted Conf | Action |
|----------|---------------|---------------|-----------------|---------|
| F01      | 0.75 (75%)   | 0.80          | 0.60           | Store   |
| F02      | 0.40 (40%)   | 0.70          | 0.28           | Ignore  |
| F03      | 0.90 (90%)   | 0.50          | 0.45           | Store   |
| F04      | 0.20 (20%)   | 0.90          | 0.18           | Ignore  |

## Benefits

1. **Self-Learning**: Poor performing formulas get penalized automatically
2. **Quality Filter**: Only signals with sufficient experience-based confidence reach UI
3. **Adaptive**: As formulas improve, their signals gain more weight
4. **Risk Management**: Low-confidence signals filtered out before trading decisions
5. **Performance Tracking**: Continuous monitoring of formula effectiveness

## Integration Points

- **No changes needed** to existing WebSocket logic
- **No changes needed** to FastAPI endpoints  
- **No changes needed** to market data fetching
- **Only formula signal generation** needs to call `store_formula_signal()`

The AI system now actively learns and filters signals based on real performance! 🎯
