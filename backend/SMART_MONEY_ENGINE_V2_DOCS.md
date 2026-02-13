# SmartMoneyEngine v2 - Statistically Stable Implementation

## Overview

SmartMoneyEngine v2 is a hardened, statistically stable version of the SmartMoneyEngine with proper feature normalization, minimum activation thresholds, and robust confidence scoring using sigmoid functions. This version ensures no spurious signals and provides reliable directional bias predictions.

## Key Improvements Over v1

### 1. Feature Normalization
- **OI Acceleration**: Normalized by total OI to avoid raw contract number bias
- **PCR Shift**: Uses Z-score calculation over last 30 snapshots for statistical significance
- **Straddle Change**: Normalized to 0-1 range with 50% change cap
- **Volume Ratio**: Current volume vs 15-minute average for relative activity

### 2. Minimum Activation Thresholds
Engine only generates directional signals when:
- **Minimum Snapshots**: ≥ 10 snapshots (configurable)
- **Data Freshness**: < 2 minutes old
- **OI Change Threshold**: > 5,000 total OI change
- **Volume Ratio**: > 0.8 (80% of recent average)

### 3. Statistical Confidence Scoring
- **Sigmoid Function**: `confidence = sigmoid(weighted_sum) * 100`
- **Weighted Features**: Each normalized feature contributes proportionally
- **Conflict Detection**: Confidence decreases sharply with conflicting signals

### 4. Robust IV Regime Classification
- **Historical Data**: Requires ≥ 75 snapshots (1 full trading day)
- **Percentile-Based**: 30th/70th percentile thresholds
- **Fallback**: Returns "NORMAL" with insufficient data

## Feature Normalization Details

### OI Acceleration Normalization
```python
# Raw acceleration
acceleration = current_oi_delta - previous_oi_delta

# Normalized by total OI
oi_acceleration_ratio = acceleration / total_oi
```

### PCR Z-Score Calculation
```python
# Calculate PCR for each timestamp
pcr_values = [calculate_pcr(snapshot) for snapshot in snapshots]

# Z-score calculation
current_pcr = pcr_values[0]
mean_pcr = np.mean(pcr_values[1:])
std_pcr = np.std(pcr_values[1:])

pcr_z = (current_pcr - mean_pcr) / std_pcr
```

### Straddle Change Normalization
```python
# Percentage change
pct_change = abs((current_straddle - previous_straddle) / previous_straddle)

# Normalize to 0-1 range (cap at 50%)
straddle_normalized = min(pct_change / 0.5, 1.0)
```

### Volume Ratio
```python
# Current volume
current_volume = sum(snapshot.volume for snapshot in latest_snapshots)

# 15-minute average
avg_volume_15min = calculate_average_volume(snapshots, minutes=15)

# Volume ratio
volume_ratio = current_volume / avg_volume_15min
```

## Confidence Scoring Formula

### Sigmoid Function
```python
def sigmoid_confidence(weighted_sum: float) -> float:
    """
    Calculate confidence using sigmoid function
    Range: 0-1, scaled to 0-100
    """
    scaled_input = weighted_sum * 2  # Scale for appropriate curve
    sigmoid_value = 1 / (1 + math.exp(-scaled_input))
    return max(0, min(1, sigmoid_value))
```

### Feature Weights
- **PCR Z-Score**: Direct contribution (positive/negative)
- **OI Acceleration**: `ratio * 100` (amplified for significance)
- **Straddle Change**: `normalized * 2` (directional)
- **Volume Ratio**: `(ratio - 1) * 2` (activity bonus)
- **PCR Level**: ±1 for extreme levels

## Activation Thresholds

### Data Quality Checks
```python
def check_activation_thresholds(snapshots, symbol):
    # Minimum snapshot count
    if len(set(s.timestamp for s in snapshots)) < min_snapshots:
        return INSUFFICIENT_DATA
    
    # Data freshness
    if (now() - latest_timestamp) > max_data_age:
        return STALE_DATA
    
    # OI change threshold
    total_oi_change = sum(abs(s.oi_change) for s in snapshots)
    if total_oi_change < min_oi_change_threshold:
        return LOW_ACTIVITY
    
    # Volume ratio
    if volume_ratio < min_volume_ratio:
        return LOW_VOLUME
```

### Response Structure
```json
{
  "bias": "NEUTRAL",
  "confidence": 0.0,
  "reasoning": ["Insufficient data for directional signal: Low volume ratio: 0.15 < 0.8"],
  "data_quality": {
    "status": "insufficient_data",
    "reason": "Low volume ratio: 0.15 < 0.8"
  }
}
```

## API Endpoints

### V2 Signal Generation
```
GET /api/v1/options/smart-money-v2/{symbol}
```

**Response Format:**
```json
{
  "status": "success",
  "data": {
    "symbol": "NIFTY",
    "timestamp": "2026-02-11T17:33:49.825381+00:00",
    "bias": "NEUTRAL",
    "confidence": 0.0,
    "metrics": {
      "pcr": 0.0,
      "pcr_shift_z": 0.0,
      "atm_straddle": 0.0,
      "straddle_change_normalized": 0.0,
      "oi_acceleration_ratio": 0.0,
      "volume_ratio": 0.0,
      "iv_regime": "NORMAL"
    },
    "reasoning": ["Insufficient data for directional signal: Low volume ratio: 0.15 < 0.8"],
    "data_quality": {
      "snapshot_count": 15,
      "data_freshness_minutes": 0.5,
      "total_oi": 180000,
      "expiry_date": "2026-02-27"
    }
  }
}
```

### Performance Tracking
```
GET /api/v1/options/smart-money/performance/{symbol}?days=30
```

**Response Format:**
```json
{
  "status": "success",
  "data": {
    "symbol": "NIFTY",
    "period_days": 30,
    "total_signals": 0,
    "directional_signals": 0,
    "completed_signals": 0,
    "win_rate": 0.0,
    "last_7_day_accuracy": 0.0,
    "bias_distribution": {"BULLISH": 0, "BEARISH": 0, "NEUTRAL": 0},
    "average_confidence_by_bias": {},
    "iv_regime_performance": {
      "LOW": {"total_signals": 0, "completed_signals": 0, "win_rate": 0, "average_confidence": 0},
      "NORMAL": {"total_signals": 0, "completed_signals": 0, "win_rate": 0, "average_confidence": 0},
      "HIGH": {"total_signals": 0, "completed_signals": 0, "win_rate": 0, "average_confidence": 0}
    },
    "recent_predictions": []
  }
}
```

### Result Updates
```
POST /api/v1/options/smart-money/update-results/{symbol}?lookback_minutes=30
```

## Database Schema

### SmartMoneyPredictions Table
```sql
CREATE TABLE smart_money_predictions (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    symbol VARCHAR NOT NULL,
    bias VARCHAR NOT NULL,
    confidence FLOAT NOT NULL,
    
    -- Normalized metrics
    pcr FLOAT,
    pcr_shift_z FLOAT,
    atm_straddle FLOAT,
    straddle_change_normalized FLOAT,
    oi_acceleration_ratio FLOAT,
    iv_regime VARCHAR,
    
    -- Performance tracking
    actual_move FLOAT,
    result VARCHAR,  -- CORRECT, WRONG, NEUTRAL
    
    -- Metadata
    model_version VARCHAR DEFAULT 'v2.0',
    expiry_date VARCHAR
);
```

### Indexes for Performance
```sql
CREATE INDEX idx_smart_money_predictions_symbol ON smart_money_predictions(symbol);
CREATE INDEX idx_smart_money_predictions_timestamp ON smart_money_predictions(timestamp);
CREATE INDEX idx_smart_money_predictions_symbol_timestamp ON smart_money_predictions(symbol, timestamp);
CREATE INDEX idx_smart_money_predictions_result ON smart_money_predictions(result);
```

## Validation Checklist

### ✅ Statistical Stability
- [x] All features normalized before bias calculation
- [x] No raw contract numbers influence decisions
- [x] Z-score based PCR shift calculation
- [x] Bounded straddle change (0-1 range)
- [x] Relative volume ratio calculation

### ✅ Activation Thresholds
- [x] Minimum snapshot count enforcement
- [x] Data freshness validation (< 2 minutes)
- [x] OI change threshold (> 5,000)
- [x] Volume ratio requirement (> 0.8)
- [x] Graceful NEUTRAL responses

### ✅ Confidence Scoring
- [x] Sigmoid function implementation
- [x] Weighted feature combination
- [x] 0-100 range enforcement
- [x] Conflict signal detection
- [x] Non-linear scaling

### ✅ IV Regime Classification
- [x] 1+ trading day historical data requirement
- [x] Percentile-based thresholds (30/70)
- [x] Proper fallback to "NORMAL"
- [x] Historical data validation

### ✅ Expiry Safety
- [x] Nearest weekly expiry selection
- [x] No expiry mixing in calculations
- [x] Auto-rollover capability
- [x] Expiry date tracking

### ✅ Data Validation
- [x] Null value detection
- [x] Negative OI prevention
- [x] Zero division protection
- [x] Timestamp ordering validation
- [x] Comprehensive error handling

### ✅ Performance Tracking
- [x] Historical prediction storage
- [x] Result calculation and updates
- [x] Win rate accuracy tracking
- [x] IV regime performance analysis
- [x] Bias distribution metrics

## Production Deployment

### Configuration
```python
engine = SmartMoneyEngineV2(
    snapshot_count=30,      # Historical snapshots for analysis
    min_snapshots=10,       # Minimum for activation
    min_oi_change_threshold=5000,  # Minimum OI activity
    min_volume_ratio=0.8,   # Minimum relative volume
    max_data_age_minutes=2    # Maximum data age
)
```

### Monitoring
- Activation threshold triggers
- Normalization bounds validation
- Confidence distribution monitoring
- Performance metrics tracking
- Data quality alerts

### Scaling Considerations
- Database connection pooling
- Cached result management (30-second TTL)
- Batch performance updates
- Historical data archiving
- Real-time monitoring dashboards

## Usage Examples

### Basic Signal Generation
```python
from app.services.market_data.smart_money_engine_v2 import SmartMoneyEngineV2

engine = SmartMoneyEngineV2()
signal = await engine.generate_smart_money_signal("NIFTY", db_session)

if signal['confidence'] > 0:
    print(f"Directional signal: {signal['bias']} (confidence: {signal['confidence']})")
else:
    print(f"No signal: {signal['reasoning'][0]}")
```

### Performance Analysis
```python
from app.services.market_data.performance_tracking_service import PerformanceTrackingService

perf_service = PerformanceTrackingService()
performance = await perf_service.get_performance_metrics("NIFTY", db, days=30)

print(f"Win Rate: {performance['win_rate']}%")
print(f"7-Day Accuracy: {performance['last_7_day_accuracy']}%")
```

---

**Status**: ✅ Production Ready  
**Version**: v2.0  
**Focus**: Statistical Stability & Normalization  
**Last Updated**: 2026-02-11  
**Author**: Senior Quantitative Engineer
